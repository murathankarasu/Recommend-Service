import logging
from typing import Dict, List, Any
from datetime import datetime
from config.config import (
    COLLECTION_USERS,
    COLLECTION_USER_PATTERNS,
    COLLECTION_USER_EMOTION_HISTORY,
    USER_PROFILE_FACTORS,
    BEHAVIOR_ANALYSIS
)
from services.firebase_services.firebase_base import FirebaseBase

logger = logging.getLogger(__name__)

class UserProfileManager:
    def __init__(self, firebase_service: FirebaseBase):
        self.firebase = firebase_service
        self.emotion_history = {}  # Kullanıcı bazlı duygu geçmişi

    def _calculate_user_profile_score(self, user_data: Dict[str, Any]) -> float:
        """Kullanıcı profil skorunu hesaplar"""
        score = 0
        for factor, weight in USER_PROFILE_FACTORS.items():
            if factor == 'interests':
                score += weight * len(user_data.get('interests', [])) / 10
            elif factor == 'demographics':
                score += weight * (1 if user_data.get('age') and user_data.get('gender') else 0.5)
            elif factor == 'behavioral_patterns':
                score += weight * len(user_data.get('behavioral_patterns', [])) / 5
            elif factor == 'social_connections':
                score += weight * len(user_data.get('social_connections', [])) / 100
        return score

    def _analyze_user_behavior(self, user_data: Dict[str, Any]) -> float:
        """Kullanıcı davranışını analiz eder"""
        behavior_score = 0
        for metric, weight in BEHAVIOR_ANALYSIS.items():
            if metric == 'session_duration':
                behavior_score += weight * min(user_data.get('avg_session_duration', 0) / 3600, 1)
            elif metric == 'scroll_depth':
                behavior_score += weight * user_data.get('avg_scroll_depth', 0.5)
            elif metric == 'interaction_patterns':
                behavior_score += weight * len(user_data.get('interaction_patterns', [])) / 10
            elif metric == 'content_preferences':
                behavior_score += weight * len(user_data.get('content_preferences', [])) / 5
        return behavior_score

    def _update_emotion_history(self, user_id: str, current_distribution: Dict[str, float]):
        """Kullanıcı duygu geçmişini günceller."""
        if user_id not in self.emotion_history:
            self.emotion_history[user_id] = current_distribution
        else:
            for emotion, value in current_distribution.items():
                old_value = self.emotion_history[user_id].get(emotion, 0.0)
                self.emotion_history[user_id][emotion] = (old_value * 0.7) + (value * 0.3)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Kullanıcı profilini getirir"""
        try:
            user_data = await self.firebase.get_user_data(user_id)
            if not user_data:
                return {}
            
            profile_score = self._calculate_user_profile_score(user_data)
            behavior_score = self._analyze_user_behavior(user_data)
            
            return {
                **user_data,
                'profile_score': profile_score,
                'behavior_score': behavior_score,
                'emotion_history': self.emotion_history.get(user_id, {})
            }
            
        except Exception as e:
            logger.error(f"Kullanıcı profili getirilirken hata: {str(e)}")
            return {}

    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Kullanıcı profilini günceller"""
        try:
            await self.firebase.update_user_data(user_id, updates)
            return True
        except Exception as e:
            logger.error(f"Kullanıcı profili güncellenirken hata: {str(e)}")
            return False

    def get_emotion_history(self, user_id: str) -> Dict[str, float]:
        """Kullanıcının duygu geçmişini getirir"""
        return self.emotion_history.get(user_id, {})

    def clear_emotion_history(self, user_id: str):
        """Kullanıcının duygu geçmişini temizler"""
        if user_id in self.emotion_history:
            del self.emotion_history[user_id] 