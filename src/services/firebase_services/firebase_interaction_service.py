from datetime import datetime
from typing import Dict, List
from .firebase_base import FirebaseBase
from config import COLLECTION_INTERACTIONS, COLLECTION_POSTS
import logging
import traceback

class FirebaseInteractionService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.collection_name = "userEmotionInteractions"
        self.logger = logging.getLogger(__name__)

    async def get_user_interactions(self, user_id: str) -> List[Dict]:
        """Kullanıcının etkileşimlerini Firestore'dan alır"""
        try:
            print(f"[FirebaseService] Kullanıcı etkileşimleri alınıyor - Kullanıcı: {user_id}")
            
            interactions = []
            docs = self.db.collection(self.collection_name).where("userId", "==", user_id).stream()
            
            for doc in docs:
                interaction = doc.to_dict()
                interaction['id'] = doc.id
                interactions.append(interaction)
            
            print(f"[FirebaseService] Filtrelenmiş etkileşimler: {interactions}")
            return interactions
                
        except Exception as e:
            print(f"[FirebaseService ERROR] Etkileşimler alınırken hata oluştu: {str(e)}")
            return []

    async def add_interaction(
        self,
        user_id: str,
        content_id: str,
        interaction_type: str,
        emotion: str,
        confidence: float = 0.5
    ) -> bool:
        """Yeni bir etkileşim ekler"""
        try:
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M:%S %p UTC+3")
            
            data = {
                "userId": user_id,
                "postId": content_id,
                "interactionType": interaction_type,
                "emotion": emotion,
                "confidence": confidence,
                "timestamp": timestamp
            }
            
            print(f"[FirebaseService DEBUG] Gönderilen veri: {data}")
            
            doc_ref = self.db.collection(self.collection_name).document()
            doc_ref.set(data)
            
            print("[FirebaseService] Etkileşim başarıyla eklendi")
            return True
            
        except Exception as e:
            error_msg = f"Etkileşim ekleme hatası: {str(e)}"
            print(f"[FirebaseService ERROR] {error_msg}")
            print(f"[FirebaseService ERROR] Hata detayı: {traceback.format_exc()}")
            self.logger.error(error_msg)
            return False

    async def get_user_emotion_data(self, user_id: str) -> Dict:
        """Kullanıcının duygu verilerini getirir"""
        try:
            interactions = await self.get_user_interactions(user_id)
            
            result = {
                'interactions': interactions,
                'last_updated': datetime.now()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kullanıcı verisi getirme hatası: {str(e)}")
            raise

    async def log_interaction(self, user_id: str, content_id: str, 
                        interaction_type: str, emotion: str, 
                        weight: float, is_ad: bool = False) -> None:
        """Etkileşimi kaydet ve reklam ise metrikleri güncelle"""
        try:
            data = {
                "user_id": user_id,
                "content_id": content_id,
                "type": interaction_type,
                "emotion": emotion,
                "weight": weight,
                "confidence": weight,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "is_ad": is_ad
            }
            
            doc_ref = self.db.collection(self.collection_name).document()
            doc_ref.set(data)
            
            if is_ad:
                await self._update_ad_metrics(content_id, interaction_type, emotion)
            else:
                post = await self.get_collection(COLLECTION_POSTS)
                post = next((p for p in post if p['id'] == content_id), None)
                if post and post.get('tags', {}).get('advertise', False):
                    await self._update_ad_metrics(content_id, interaction_type, emotion)
                    
        except Exception as e:
            self.logger.error(f"Etkileşim kaydedilirken hata: {str(e)}")
            raise 