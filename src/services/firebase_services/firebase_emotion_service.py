from datetime import datetime
from typing import Dict, List, Optional
from .firebase_base import FirebaseBase
from config import COLLECTION_USER_EMOTION_HISTORY, COLLECTION_USER_PATTERNS
import logging

class FirebaseEmotionService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_user_emotion_history(self, user_id: str) -> List[Dict]:
        """Kullanıcının duygu geçmişini Firestore'dan alır"""
        try:
            emotions = []
            docs = self.db.collection(COLLECTION_USER_EMOTION_HISTORY).where("user_id", "==", user_id).stream()
            
            for doc in docs:
                emotion_data = doc.to_dict()
                emotion_data['id'] = doc.id
                emotions.append(emotion_data)
            
            return emotions
        except Exception as e:
            self.logger.error(f"Duygu geçmişi alınırken hata: {str(e)}")
            return []

    def add_emotion_data(self, user_id: str, emotion_data: Dict) -> bool:
        """Yeni duygu verisi ekler"""
        try:
            data = {
                "user_id": user_id,
                **emotion_data,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            
            doc_ref = self.db.collection(COLLECTION_USER_EMOTION_HISTORY).document()
            doc_ref.set(data)
            return True
        except Exception as e:
            self.logger.error(f"Duygu verisi eklenirken hata: {str(e)}")
            return False

    def get_user_pattern(self, user_id: str) -> Optional[Dict]:
        """Kullanıcının duygu pattern'ini getirir"""
        try:
            doc = self.db.collection(COLLECTION_USER_PATTERNS).document(user_id).get()
            if doc.exists:
                pattern_data = doc.to_dict()
                pattern_data['id'] = doc.id
                return pattern_data
            return None
        except Exception as e:
            self.logger.error(f"Pattern alınırken hata: {str(e)}")
            return None

    def update_user_pattern(self, user_id: str, pattern: Dict) -> bool:
        """Kullanıcının duygu pattern'ini günceller"""
        try:
            data = {
                "user_id": user_id,
                "pattern": pattern,
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            
            doc_ref = self.db.collection(COLLECTION_USER_PATTERNS).document(user_id)
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Pattern güncellenirken hata: {str(e)}")
            return False

    def get_emotion_statistics(self, user_id: str) -> Dict:
        """Kullanıcının duygu istatistiklerini hesaplar"""
        try:
            emotions = self.get_user_emotion_history(user_id)
            
            if not emotions:
                return {}
            
            # Duygu dağılımını hesapla
            emotion_counts = {}
            total_emotions = len(emotions)
            
            for emotion_data in emotions:
                emotion = emotion_data.get('emotion')
                if emotion:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Yüzdeleri hesapla
            emotion_percentages = {
                emotion: (count / total_emotions) * 100
                for emotion, count in emotion_counts.items()
            }
            
            return {
                'total_interactions': total_emotions,
                'emotion_distribution': emotion_percentages,
                'last_updated': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
        except Exception as e:
            self.logger.error(f"İstatistikler hesaplanırken hata: {str(e)}")
            return {} 