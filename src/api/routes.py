from flask import Blueprint, request, jsonify
from services.firebase_service import FirebaseService
from services.recommendation_service import RecommendationService
from models.emotion_model import EmotionModel
import asyncio
import logging
import os

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Servisleri başlat
firebase_service = FirebaseService()
recommendation_service = RecommendationService()
emotion_model = EmotionModel()

@api_bp.route('/recommendations/<user_id>', methods=['GET'])
async def get_recommendations(user_id):
    try:
        recommendations = await recommendation_service.get_recommendations(user_id)
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/update-patterns/<user_id>', methods=['POST'])
async def update_patterns(user_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        await recommendation_service.update_user_patterns(user_id, data)
        return jsonify({'message': 'Patterns updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/log-interaction', methods=['POST'])
async def log_interaction():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        ad_id = data.get('ad_id')
        interaction_type = data.get('interaction_type')
        emotion = data.get('emotion')
        intensity = data.get('intensity', 1.0)
        
        await firebase_service.log_ad_interaction(
            user_id, ad_id, interaction_type, emotion, intensity
        )
        
        return jsonify({'message': 'Interaction logged successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/feed/<user_id>', methods=['GET'])
async def get_unified_feed(user_id):
    """Kullanıcı için birleştirilmiş feed akışını döndürür"""
    try:
        # Kullanıcı verilerini al
        user_data = await firebase_service.get_user_emotion_data(user_id)
        interactions = user_data.get('interactions', [])

        # Cold start kontrolü
        if len(interactions) < recommendation_service.cold_start_threshold:
            # Yeni kullanıcı için rastgele içerik
            feed = await recommendation_service.get_user_feed(user_id)
            return jsonify({
                'status': 'success',
                'data': {
                    'feed': feed,
                    'is_cold_start': True,
                    'message': 'Yeni kullanıcı için öneriler'
                }
            }), 200

        # Normal kullanıcı için kişiselleştirilmiş içerik
        feed = await recommendation_service.get_user_feed(user_id)
        
        # Kullanıcı pattern'ini al
        pattern = await firebase_service.get_user_pattern(user_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'feed': feed,
                'is_cold_start': False,
                'user_pattern': pattern,
                'message': 'Kişiselleştirilmiş öneriler'
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Feed oluşturma hatası: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Feed oluşturulurken bir hata oluştu',
            'error': str(e)
        }), 500 