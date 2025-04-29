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

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        print(f"[API] Öneri isteği alındı - Kullanıcı ID: {user_id}")
        
        # Kullanıcı etkileşimlerini getir
        print("[API] Kullanıcı etkileşimleri getiriliyor...")
        user_interactions = run_async(firebase.get_user_interactions(user_id))
        print(f"[API] Kullanıcı etkileşimleri alındı: {len(user_interactions)} adet etkileşim")
        
        if not user_interactions:
            print("[API] Kullanıcı etkileşimi bulunamadı")
            return jsonify({
                'success': False,
                'error': 'Kullanıcı etkileşimi bulunamadı',
                'recommendations': [],
                'emotion_pattern': {}
            })
        
        # Duygu desenini analiz et
        print("[API] Duygu deseni analiz ediliyor...")
        emotion_pattern = emotion_analyzer.analyze_pattern(user_interactions, user_id)
        print(f"[API] Duygu deseni analiz edildi: {emotion_pattern}")
        
        # İçerikleri getir
        print("[API] İçerikler getiriliyor...")
        contents = run_async(firebase_post.get_all_posts())
        
        # İçerik karışımını oluştur
        content_mix = content_recommender.get_content_mix(contents, emotion_pattern, 20)
        
        # Reklamları ekle
        final_mix = run_async(ad_manager.insert_ads(content_mix, user_id))
        
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