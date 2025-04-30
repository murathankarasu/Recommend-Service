from flask import Flask, request, jsonify
from flask_cors import CORS
from services.firebase_services.firebase_interaction_service import FirebaseInteractionService
from services.firebase_services.firebase_post_service import FirebasePostService
from models.emotion_analyzer import EmotionAnalyzer
from models.content_recommender import ContentRecommender
from models.ad_manager import AdManager
from models.word_analyzer import WordAnalyzer
from models.user_profile_manager import UserProfileManager
from models.performance_monitor import PerformanceMonitor
from config.config import (
    COLLECTION_USERS,
    COLLECTION_POSTS,
    COLLECTION_INTERACTIONS,
    COLLECTION_USER_PATTERNS,
    API_HOST,
    API_PORT,
    EMOTION_CATEGORIES
)
import os
import traceback
import asyncio
# --- Yardımcı modüller ---
from services.reccomend_service.user_history_utils import get_recent_shown_post_ids
from services.reccomend_service.ab_test_logger import log_recommendation_event
from services.reccomend_service.cold_start_utils import get_cold_start_content
from services.reccomend_service.date_utils import parse_timestamp
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app)

# Servisleri başlat
firebase = FirebaseInteractionService()
firebase_post = FirebasePostService()
emotion_analyzer = EmotionAnalyzer()
content_recommender = ContentRecommender()
ad_manager = AdManager(firebase)
word_analyzer = WordAnalyzer()
user_profile_manager = UserProfileManager(firebase)
performance_monitor = PerformanceMonitor()

MAX_FEED_HISTORY = 100  # Her kullanıcı için maksimum feed geçmişi kaydı

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def has_interaction_with_posts(user_interactions, post_ids):
    """
    Belirtilen post_ids listesindeki içeriklere kullanıcı etkileşimi olmuş mu kontrol eder.
    Sadece like, comment, emotion gibi etkileşimler dikkate alınır.
    """
    post_ids_set = set(post_ids)
    valid_types = {'like', 'comment', 'emotion'}
    for interaction in user_interactions:
        pid = interaction.get('postId') or interaction.get('content_id') or interaction.get('id')
        if pid in post_ids_set:
            if interaction.get('interactionType') in valid_types:
                return True
    return False

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        now = datetime.now(timezone.utc)
        # 1. Son aktiviteyi Firestore'dan çek
        last_active_doc = firebase.db.collection('userFeedLastActive').document(user_id).get()
        last_active = None
        if last_active_doc.exists:
            last_active = last_active_doc.to_dict().get('last_active')
            if last_active:
                last_active = datetime.fromisoformat(last_active)
        # 2. 10 dakikadan fazla geçtiyse feed geçmişini sil
        if last_active and (now - last_active) > timedelta(minutes=10):
            shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).stream()
            for doc in shown_feed_docs:
                firebase.db.collection('userShownFeeds').document(doc.id).delete()
            print(f"[API] Kullanıcı {user_id} için eski feed geçmişi silindi.")
            shown_post_ids = []
        else:
            shown_post_ids = []
            try:
                shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').limit(100).stream()
                for doc in shown_feed_docs:
                    data = doc.to_dict()
                    shown_post_ids.extend(data.get('post_ids', []))
            except Exception as e:
                print(f"[API] shown_post_ids çekilemedi: {e}")
        # 3. Son aktiviteyi güncelle
        firebase.db.collection('userFeedLastActive').document(user_id).set({'last_active': now.isoformat()})
        # Kullanıcı etkileşimlerini getir
        print("[API] Kullanıcı etkileşimleri getiriliyor...")
        user_interactions = run_async(firebase.get_user_interactions(user_id))
        print(f"[API] Kullanıcı etkileşimleri alındı: {len(user_interactions)} adet etkileşim")
        # İçerikleri getir
        print("[API] İçerikler getiriliyor...")
        contents = run_async(firebase_post.get_all_posts())
        # Eğer hiç etkileşim yoksa soğuk başlangıç önerisi
        if not user_interactions:
            print("[API] Soğuk başlangıç önerisi hazırlanıyor...")
            content_mix = get_cold_start_content(contents, list(EMOTION_CATEGORIES.values()), 20)
            emotion_pattern = {e: 1/len(EMOTION_CATEGORIES) for e in EMOTION_CATEGORIES.values()}
        else:
            # Duygu desenini analiz et
            print("[API] Duygu deseni analiz ediliyor...")
            emotion_pattern = emotion_analyzer.analyze_pattern(user_interactions, user_id)
            print(f"[API] Duygu deseni analiz edildi: {emotion_pattern}")
            # --- FEED ESNETME MANTIĞI ---
            # Son feeddeki içeriklere etkileşim var mı kontrol et
            if shown_post_ids:
                interacted = has_interaction_with_posts(user_interactions, shown_post_ids[-20:])
                if not interacted:
                    dominant = max(emotion_pattern, key=emotion_pattern.get)
                    n_other = len(emotion_pattern) - 1
                    for e in emotion_pattern:
                        if e == dominant:
                            emotion_pattern[e] = 0.5
                        else:
                            emotion_pattern[e] = 0.5 / n_other if n_other > 0 else 0.0
                    print(f"[API] FEED ESNETİLDİ: {emotion_pattern}")
            # İçerik karışımını oluştur (daha önce gösterilenleri hariç tut)
            content_mix = content_recommender.get_content_mix(contents, emotion_pattern, 20, shown_post_ids=shown_post_ids)
            # Eğer hiç unseen içerik kalmadıysa (feed boşsa), shown_post_ids'i sıfırla ve tekrar oluştur
            if not content_mix:
                print(f"[API] Kullanıcı {user_id} için hiç unseen içerik kalmadı, feed geçmişi sıfırlanıyor...")
                shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).stream()
                for doc in shown_feed_docs:
                    firebase.db.collection('userShownFeeds').document(doc.id).delete()
                shown_post_ids = []
                content_mix = content_recommender.get_content_mix(contents, emotion_pattern, 20, shown_post_ids=shown_post_ids)
        # Reklamları ekle
        final_mix = run_async(ad_manager.insert_ads(content_mix, user_id))
        # --- GÖSTERİLEN FEED'İ KAYDET ---
        try:
            feed_post_ids = [c['id'] for c in final_mix if 'id' in c]
            firebase.db.collection('userShownFeeds').add({
                'user_id': user_id,
                'post_ids': feed_post_ids,
                'timestamp': now.isoformat()
            })
            print(f"[API] Feed gösterimi kaydedildi: {feed_post_ids}")
        except Exception as e:
            print(f"[API] Feed gösterimi kaydedilemedi: {e}")
        # Loglama (A/B test ve parametre takibi)
        try:
            log_recommendation_event(
                user_id=user_id,
                recommended_posts=[c['id'] for c in final_mix if 'id' in c],
                params={"repeat_ratio": 0.2, "cold_start": not bool(user_interactions)}
            )
        except Exception as logerr:
            print(f"[API] Loglama hatası: {logerr}")
        # Feed geçmişi limiti kontrolü ve eski kayıtların silinmesi
        shown_feed_docs_list = list(firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').stream())
        if len(shown_feed_docs_list) > MAX_FEED_HISTORY:
            for doc in shown_feed_docs_list[MAX_FEED_HISTORY:]:
                firebase.db.collection('userShownFeeds').document(doc.id).delete()
            print(f"[API] Kullanıcı {user_id} için eski feed kayıtları limit nedeniyle silindi.")
        return jsonify({
            'success': True,
            'recommendations': final_mix,
            'emotion_pattern': emotion_pattern
        })
        
    except Exception as e:
        print(f"[API ERROR] Öneri getirme hatası: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendations': [],
            'emotion_pattern': {}
        }), 500

@app.route('/api/track_interaction', methods=['POST'])
def track_interaction():
    try:
        data = request.get_json()
        print(f"[API] Etkileşim kaydediliyor: {data}")
        
        # Gerekli alanları kontrol et
        required_fields = ['userId', 'postId', 'emotion', 'interactionType']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Eksik alan: {field}'
                }), 400
        
        # Etkileşimi kaydet
        try:
            success = run_async(firebase.add_interaction(
                user_id=data['userId'],
                content_id=data['postId'],
                interaction_type=data['interactionType'],
                emotion=data['emotion'],
                confidence=data.get('confidence', 0.5)
            ))
            
            print(f"[API] Etkileşim kaydedildi: {success}")
            
            if success:
                # İçerik etkileşimini güncelle
                content_recommender.update_content_engagement(
                    data['postId'],
                    data['interactionType']
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Etkileşim başarıyla kaydedildi'
                })
            else:
                print("[API] Etkileşim kaydedilemedi")
                return jsonify({
                    'success': False,
                    'error': 'Etkileşim kaydedilemedi'
                }), 500
            
        except Exception as e:
            print(f"[API ERROR] Etkileşim kaydetme hatası: {str(e)}")
            print(f"[API ERROR] Hata detayı: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        
    except Exception as e:
        print(f"[API ERROR] Etkileşim kaydetme hatası: {str(e)}")
        print(f"[API ERROR] Hata detayı: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host=API_HOST, port=API_PORT, debug=True) 