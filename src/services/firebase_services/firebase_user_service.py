from typing import Dict, List, Optional
from typing import Any
from .firebase_base import FirebaseBase
from config import COLLECTION_USERS, COLLECTION_USER_PATTERNS, COLLECTION_USER_EMOTION_HISTORY
import logging

class FirebaseUserService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.collection_name = COLLECTION_USERS
        self.logger = logging.getLogger(__name__)

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Kullanıcı bilgilerini Firestore'dan alır"""
        try:
            doc = self.db.collection(self.collection_name).document(user_id).get()
            if doc.exists:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            return None
        except Exception as e:
            self.logger.error(f"Kullanıcı bilgileri alınırken hata: {str(e)}")
            return None

    def update_user(self, user_id: str, data: Dict) -> bool:
        """Kullanıcı bilgilerini günceller"""
        try:
            doc_ref = self.db.collection(self.collection_name).document(user_id)
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı güncellenirken hata: {str(e)}")
            return False

    def get_all_users(self) -> List[Dict]:
        """Tüm kullanıcıları getirir"""
        try:
            users = []
            docs = self.db.collection(self.collection_name).stream()
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                users.append(user_data)
            return users
        except Exception as e:
            self.logger.error(f"Kullanıcılar alınırken hata: {str(e)}")
            return []

    def delete_user(self, user_id: str) -> bool:
        """Kullanıcıyı siler"""
        try:
            self.db.collection(self.collection_name).document(user_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı silinirken hata: {str(e)}")
            return False

    def get_user_pattern(self, user_id: str):
        """Kullanıcının güncel pattern'ini getir"""
        try:
            url = f"{self.base_url}/{COLLECTION_USER_PATTERNS}/{user_id}?key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            
            doc = response.json()
            if not doc:
                return None
                
            fields = doc.get('fields', {})
            pattern = fields.get('pattern', {}).get('mapValue', {}).get('fields', {})
            return self._convert_fields(pattern)
        except Exception as e:
            raise Exception(f"Pattern alınırken hata oluştu: {str(e)}")

    def update_user_pattern(self, user_id: str, pattern: Dict[str, Any]) -> None:
        """Kullanıcının duygu pattern'ini günceller"""
        try:
            doc_id = user_id
            url = f"{self.base_url}/{COLLECTION_USER_PATTERNS}/{doc_id}?key={self.api_key}"
            
            data = {
                "fields": {
                    "user_id": {"stringValue": user_id},
                    "pattern": {"mapValue": {"fields": pattern}},
                    "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
                }
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Kullanıcı pattern'i güncellenirken hata: {str(e)}")

    def add_user_emotion(self, user_id: str, emotion_data: dict):
        """Kullanıcıya yeni duygu verisi ekle"""
        try:
            url = f"{self.base_url}/{COLLECTION_USERS}/{user_id}?key={self.api_key}"
            
            response = requests.get(url)
            user_data = response.json().get('fields', {}) if response.status_code == 200 else {}
            
            emotion_data['timestamp'] = datetime.now().isoformat() + "Z"
            if 'emotion_data' not in user_data:
                user_data['emotion_data'] = {"arrayValue": {"values": []}}
            
            user_data['emotion_data']['arrayValue']['values'].append({
                "mapValue": {
                    "fields": {
                        k: {"stringValue": v} if isinstance(v, str) else {"doubleValue": v} if isinstance(v, float) else {"integerValue": v} for k, v in emotion_data.items()
                    }
                }
            })
            
            data = {"fields": user_data}
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            return True
        except Exception as e:
            raise Exception(f"Duygu verisi eklenirken hata oluştu: {str(e)}")

    def update_user_emotion_history(self, user_id: str, emotion_data: Dict) -> None:
        """Kullanıcı duygu geçmişini günceller"""
        try:
            url = f"{self.base_url}/{COLLECTION_USER_EMOTION_HISTORY}/{user_id}?key={self.api_key}"
            
            data = {
                "fields": {
                    **{k: {"stringValue": v} if isinstance(v, str) else {"doubleValue": v} if isinstance(v, float) else {"integerValue": v} for k, v in emotion_data.items()},
                    "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
                }
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Kullanıcı duygu geçmişi güncellenirken hata: {str(e)}") 