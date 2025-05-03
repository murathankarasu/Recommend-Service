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
    EMOTION_CATEGORIES,
    OPPOSITE_EMOTIONS
)
import os
import traceback
import asyncio
import base64
# --- Yardımcı modüller ---
from services.reccomend_service.user_history_utils import get_recent_shown_post_ids
from services.reccomend_service.ab_test_logger import log_recommendation_event
from services.reccomend_service.cold_start_utils import get_cold_start_content
from services.reccomend_service.date_utils import parse_timestamp
from datetime import datetime, timezone, timedelta
import time

app = Flask(__name__)
CORS(app)

# Railway veya başka bir ortamda FIREBASE_CREDENTIALS değişkeni varsa dosyaya yaz
firebase_creds_b64 = os.getenv("FIREBASE_CREDENTIALS")
if firebase_creds_b64:
    creds_path = os.path.join(os.path.dirname(__file__), "config", "lorien-app-tr-firebase-adminsdk.json")
    os.makedirs(os.path.dirname(creds_path), exist_ok=True)
    with open(creds_path, "wb") as f:
        f.write(base64.b64decode(firebase_creds_b64))

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
DOMINANT_EMOTION_THRESHOLD = 0.6 # Threshold for Scenario 2

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
    print(f"[API] /api/recommendations endpoint çağrıldı: user_id={user_id}")
    try:
        now = datetime.now(timezone.utc)
        # 1. Son aktivite ve feed geçmişi yönetimi (existing logic is complex, keeping as is for now)
        print("[API DEBUG] Handling last active and feed history...")
        last_active_doc = None
        try:
            last_active_doc = firebase.db.collection('userFeedLastActive').document(user_id).get()
        except Exception as get_err:
            print(f"[API ERROR] userFeedLastActive get() hatası: {get_err}")

        last_active = None
        if last_active_doc and last_active_doc.exists:
            last_active_data = last_active_doc.to_dict()
            last_active = last_active_data.get('last_active')
            if last_active:
                try:
                    last_active = datetime.fromisoformat(last_active)
                except Exception as parse_err:
                    last_active = None

        shown_post_ids = []
        if last_active and (now - last_active) > timedelta(minutes=10):
            print("[API DEBUG] Feed history older than 10 minutes. Deleting...")
            try:
                shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).stream()
                deleted_count = 0
                for doc in shown_feed_docs:
                    firebase.db.collection('userShownFeeds').document(doc.id).delete()
                    deleted_count += 1
                print(f"[API] Kullanıcı {user_id} için {deleted_count} adet eski feed geçmişi silindi.")
            except Exception as delete_err:
                print(f"[API ERROR] Eski feed geçmişi silinirken hata: {delete_err}")
        else:
            print("[API DEBUG] Fetching recent shown feeds...")
            try:
                shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').limit(100).stream()
                count = 0
                for doc in shown_feed_docs:
                    data = doc.to_dict()
                    shown_post_ids.extend(data.get('post_ids', []))
                    count += 1
                print(f"[API DEBUG] Found {count} shown feed documents. Total shown_post_ids: {len(shown_post_ids)}")
            except Exception as e:
                print(f"[API ERROR] shown_post_ids çekilemedi: {e}")

        # Update last active timestamp (existing logic)
        print("[API DEBUG] Updating last active timestamp...")
        try:
            firebase.db.collection('userFeedLastActive').document(user_id).set({'last_active': now.isoformat()})
        except Exception as update_err:
             print(f"[API ERROR] Son aktivite güncellenirken hata: {update_err}")

        # 2. Kullanıcı etkileşimlerini getir (existing logic)
        print("[API] Kullanıcı etkileşimleri getiriliyor...")
        user_interactions = []
        try:
            user_interactions = firebase.get_user_interactions(user_id)
            print(f"[API] Kullanıcı etkileşimleri alındı: {len(user_interactions)} adet etkileşim")
        except Exception as e:
            print(f"[API ERROR] Kullanıcı etkileşimleri alınamadı: {e}")

        # 3. İçerikleri getir (existing logic)
        print("[API] İçerikler getiriliyor...")
        contents = []
        try:
            contents = firebase_post.get_all_posts()
            print(f"[API] İçerikler alındı: {len(contents)} adet içerik")
        except Exception as e:
             print(f"[API ERROR] İçerikler alınamadı: {e}")

        # 4. Duygu analizi ve öneri oluşturma (UPDATED LOGIC)
        emotion_pattern = {}
        current_emotion = None
        personalized_transitions = {}
        content_mix = []
        peak_moment_index = None
        final_mix = [] # Initialize final_mix here

        if not user_interactions:
            # --- SCENARIO 1: COLD START --- #
            print("[API] COLD START: Etkileşim yok, soğuk başlangıç içeriği oluşturuluyor.")
            content_mix = get_cold_start_content(
                contents,
                list(EMOTION_CATEGORIES.values()),
                20 # Desired number of cold start items
            )
            emotion_pattern = {e: 1/len(EMOTION_CATEGORIES) for e in EMOTION_CATEGORIES.values()} # Default pattern for response
            peak_moment_index = None # No peak for cold start
            final_mix = content_mix # No ads for cold start
            print(f"[API] COLD START: {len(final_mix)} adet içerik oluşturuldu. Reklam eklenmedi.")
            # Skip directly to saving/logging/returning

        else:
            # --- SCENARIOS WITH INTERACTIONS --- #
            # Analyze pattern, current emotion, transitions (existing logic)
            emotion_pattern = emotion_analyzer.analyze_pattern(user_interactions, user_id)
            current_emotion, _ = emotion_analyzer.get_current_emotion_and_transitions(user_interactions)
            personalized_transitions = emotion_analyzer.analyze_transition_patterns(user_interactions)
            print(f"[API] Analiz: Pattern={emotion_pattern}, Current={current_emotion}, Transitions={len(personalized_transitions)}")

            # --- SCENARIO 2: DOMINANT EMOTION CHECK & ADJUSTMENT --- #
            dominant_emotion = max(emotion_pattern, key=emotion_pattern.get, default=None)
            if dominant_emotion and emotion_pattern[dominant_emotion] > DOMINANT_EMOTION_THRESHOLD:
                print(f"[API] BASKIN DUYGU TESPİTİ: {dominant_emotion} oranı (%{emotion_pattern[dominant_emotion]*100:.1f}) yüksek. Desen ayarlanıyor.")
                adjusted_pattern = emotion_pattern.copy()
                opposite_emotions = OPPOSITE_EMOTIONS.get(dominant_emotion, [])
                reduction_factor = 0.5 # How much to reduce the dominant emotion
                boost_per_opposite = (emotion_pattern[dominant_emotion] * (1 - reduction_factor)) / len(opposite_emotions) if opposite_emotions else 0

                # Reduce dominant
                adjusted_pattern[dominant_emotion] *= reduction_factor
                # Boost opposites
                for opp_emo in opposite_emotions:
                    if opp_emo in adjusted_pattern:
                        adjusted_pattern[opp_emo] += boost_per_opposite
                    else: # Should not happen if OPPOSITE_EMOTIONS and EMOTION_CATEGORIES match
                         logger.warning(f"Opposite emotion {opp_emo} not found in pattern keys.")

                # Normalize the adjusted pattern
                norm_sum = sum(adjusted_pattern.values())
                if norm_sum > 0:
                    for emo in adjusted_pattern:
                        adjusted_pattern[emo] /= norm_sum
                print(f"[API] Ayarlanmış Desen: {adjusted_pattern}")
                emotion_pattern = adjusted_pattern # Use the adjusted pattern for content mix

            # --- SCENARIO 3 Check: Feed Esnetme (Existing logic for repeated refresh without interaction) --- #
            if shown_post_ids:
                interacted = has_interaction_with_posts(user_interactions, shown_post_ids[-20:])
                if not interacted:
                    print("[API] FEED ESNETME (Etkileşimsiz Yenileme): Desen ayarlanıyor...")
                    # Standard feed esnetme logic (reduce dominant, distribute to others)
                    dominant_for_esnetme = max(emotion_pattern, key=emotion_pattern.get, default=None)
                    if dominant_for_esnetme:
                        temp_pattern = emotion_pattern.copy()
                        n_other = len(temp_pattern) - 1
                        for e in temp_pattern:
                            if e == dominant_for_esnetme:
                                temp_pattern[e] = 0.5 # Or use a different factor
                            else:
                                temp_pattern[e] = 0.5 / n_other if n_other > 0 else 0.0
                        # Normalize again
                        norm_sum = sum(temp_pattern.values())
                        if norm_sum > 0:
                            for e in temp_pattern:
                                temp_pattern[e] /= norm_sum
                        emotion_pattern = temp_pattern
                        print(f"[API] FEED ESNETME Sonrası Desen: {emotion_pattern}")

            # Get content mix using potentially adjusted pattern
            print("[API] Detaylı hikaye akışlı içerik karışımı oluşturuluyor (Ayarlanmış pattern ile)...")
            content_mix, peak_moment_index = content_recommender.get_content_mix(
                contents,
                emotion_pattern, # Use the (potentially adjusted) pattern
                limit=20,
                shown_post_ids=shown_post_ids,
                current_emotion=current_emotion,
                personalized_transitions=personalized_transitions
            )
            print(f"[API] İçerik karışımı oluşturuldu ({len(content_mix)} adet). Peak index: {peak_moment_index}")

            # Fallback for empty mix (existing logic)
            if not content_mix:
                print(f"[API] Kullanıcı {user_id} için ilk denemede içerik bulunamadı, feed geçmişi sıfırlanıp tekrar deneniyor...")
                # Delete history
                try:
                    shown_feed_docs = firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).stream()
                    for doc in shown_feed_docs:
                        firebase.db.collection('userShownFeeds').document(doc.id).delete()
                except Exception as del_err:
                     print(f"[API ERROR] Fallback feed silme hatası: {del_err}")
                shown_post_ids = []
                # Retry content mix without shown_post_ids
                content_mix, peak_moment_index = content_recommender.get_content_mix(
                    contents,
                    emotion_pattern,
                    limit=20,
                    shown_post_ids=shown_post_ids, # Now empty
                    current_emotion=current_emotion,
                    personalized_transitions=personalized_transitions
                )
                print(f"[API] Fallback sonrası içerik karışımı oluşturuldu ({len(content_mix)} adet). Peak index: {peak_moment_index}")

        # 5. Reklamları ekle (only if not cold start)
        if content_mix:
            print("[API] Stratejik reklam yerleştirme başlatılıyor...")
            ads_start = time.time()
            try:
                final_mix = ad_manager.insert_ads(
                    content_mix,
                    peak_moment_index=peak_moment_index,
                    user_id=user_id
                )
                print(f"[API] Reklam yerleştirme tamamlandı. Süre: {time.time() - ads_start:.2f} sn. Final mix: {len(final_mix)} adet.")
            except Exception as e:
                print(f"[API ERROR] insert_ads hatası: {e}")
                final_mix = content_mix # Fallback
        else:
             final_mix = []

        # 6. Gösterilen feed'i kaydet (check if final_mix exists)
        if final_mix: # Only save if we have a mix
            try:
                feed_post_ids = [c['id'] for c in final_mix if 'id' in c]
                if feed_post_ids:
                    firebase.db.collection('userShownFeeds').add({
                        'user_id': user_id,
                        'post_ids': feed_post_ids,
                        'timestamp': now.isoformat()
                    })
                    print(f"[API] Feed gösterimi kaydedildi: {len(feed_post_ids)} ID.")
                else:
                    print("[API] Kaydedilecek feed ID'si bulunamadı.")
            except Exception as e:
                print(f"[API ERROR] Feed gösterimi kaydedilemedi: {e}")
        else:
             print("[API] Gösterilecek feed bulunmadığı için kayıt yapılmadı.")

        # 7. Loglama (check if final_mix exists)
        if final_mix:
            try:
                log_recommendation_event(
                    user_id=user_id,
                    recommended_posts=[c['id'] for c in final_mix if c.get('type') != 'ad' and 'id' in c],
                    params={
                        "story_flow_enabled": bool(user_interactions), # False for cold start
                        "story_flow_type": "detailed_personalized" if user_interactions else "cold_start",
                        "peak_ad_placement": peak_moment_index is not None if user_interactions else False,
                        "cold_start": not bool(user_interactions)
                     }
                )
            except Exception as logerr:
                 print(f"[API] Loglama hatası: {logerr}")

        # 8. Feed geçmişi limiti kontrolü (always run)
        try:
            shown_feed_docs_list = list(firebase.db.collection('userShownFeeds').where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').limit(MAX_FEED_HISTORY + 5).stream())
            if len(shown_feed_docs_list) > MAX_FEED_HISTORY:
                print(f"[API] Feed history limit ({MAX_FEED_HISTORY}) reached. Deleting oldest...")
                for doc in shown_feed_docs_list[MAX_FEED_HISTORY:]:
                    firebase.db.collection('userShownFeeds').document(doc.id).delete()
        except Exception as hist_err:
            print(f"[API ERROR] Feed history cleanup error: {hist_err}")

        return jsonify({
            'success': True,
            'recommendations': final_mix,
            'emotion_pattern': emotion_pattern,
            'current_emotion': current_emotion,
            'peak_index_for_ad': peak_moment_index
        })

    except Exception as e:
        print(f"[API ERROR] Öneri getirme hatası: {str(e)}")
        traceback.print_exc() # Ana hata yakalama bloğunda traceback yazdır
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
            success = firebase.add_interaction(
                user_id=data['userId'],
                content_id=data['postId'],
                interaction_type=data['interactionType'],
                emotion=data['emotion'],
                confidence=data.get('confidence', 0.5)
            )
            
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

@app.route('/api/ping', methods=['GET'])
def ping():
    print("[API] /api/ping çağrıldı")
    return jsonify({"success": True, "message": "pong"})

if __name__ == '__main__':
    # Get host and port from environment variables or config, defaulting if not set
    host = os.getenv('API_HOST', API_HOST)
    port = int(os.getenv('PORT', API_PORT)) # PORT env var is often used by deployment platforms
    print(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=True) # debug=True for development