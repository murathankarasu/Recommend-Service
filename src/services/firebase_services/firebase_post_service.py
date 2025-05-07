from datetime import datetime, timedelta
from typing import Dict, List, Optional
from typing import Any
from .firebase_base import FirebaseBase
from config import COLLECTION_POSTS, COLLECTION_POST_METRICS
import logging
import firebase_admin
from firebase_admin import credentials, firestore

class FirebasePostService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        try:
            # Firebase Admin SDK'yı başlat
            if not firebase_admin._apps:
                cred = credentials.Certificate("config/lorien-app-tr-firebase-adminsdk.json")
                firebase_admin.initialize_app(cred)
            
            # Firestore veritabanını başlat
            self.db = firestore.client()
            print("Firebase Post servisi başarıyla başlatıldı")
        except Exception as e:
            print(f"Firebase Post servisi başlatılırken hata: {str(e)}")
            raise e

    def get_all_posts(self) -> List[Dict]:
        """Tüm postları getirir ve keyword bilgilerini ekler."""
        try:
            posts_ref = self.db.collection(COLLECTION_POSTS)
            posts = []
            
            for post in posts_ref.stream():
                post_data = post.to_dict()
                post_data['id'] = post.id
                
                # Keyword bilgilerini ekle
                if 'keywords' not in post_data:
                    post_data['keywords'] = self._extract_keywords(post_data)
                
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Postlar getirilirken hata: {str(e)}")
            return []

    def _extract_keywords(self, post_data: Dict) -> List[str]:
        """Post verilerinden keywordleri çıkarır."""
        keywords = set()
        
        # Başlıktan keyword çıkar
        if 'title' in post_data:
            title_words = post_data['title'].lower().split()
            keywords.update([w for w in title_words if len(w) > 3])
        
        # İçerikten keyword çıkar
        if 'content' in post_data:
            content_words = post_data['content'].lower().split()
            keywords.update([w for w in content_words if len(w) > 3])
        
        # Kategori ve etiketleri ekle
        if 'category' in post_data:
            keywords.add(post_data['category'].lower())
        
        if 'tags' in post_data:
            keywords.update([tag.lower() for tag in post_data['tags']])
        
        return list(keywords)

    def get_posts_by_emotion(self, emotion: str, limit: int = 20) -> List[Dict]:
        """Belirli bir duyguya sahip postları al"""
        try:
            posts = []
            docs = self.db.collection(COLLECTION_POSTS).where("emotion", "==", emotion).limit(limit).stream()
            
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Duygu bazlı postlar alınırken hata: {str(e)}")
            return []

    def get_posts_by_date(self, cutoff_date: datetime, limit: int = 10) -> List[Dict]:
        """Belirli bir tarihten sonraki postları al"""
        try:
            posts = []
            docs = self.db.collection(COLLECTION_POSTS)\
                .where("created_at", ">=", cutoff_date)\
                .order_by("created_at")\
                .limit(limit)\
                .stream()
            
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Tarih bazlı postlar alınırken hata: {str(e)}")
            return []

    def get_popular_posts(self, cutoff_date: datetime, limit: int = 10) -> List[Dict]:
        """Belirli bir tarihten sonraki popüler postları al"""
        try:
            # Post metriklerini al
            metrics = []
            docs = self.db.collection(COLLECTION_POST_METRICS)\
                .where("updated_at", ">=", cutoff_date)\
                .stream()
            
            for doc in docs:
                metric_data = doc.to_dict()
                metric_data['id'] = doc.id
                metrics.append(metric_data)
            
            # Metrikleri etkileşim sayısına göre sırala
            sorted_metrics = sorted(metrics, key=lambda x: x.get('interaction_count', 0), reverse=True)
            
            # En popüler postları getir
            popular_posts = []
            for metric in sorted_metrics[:limit]:
                post_doc = self.db.collection(COLLECTION_POSTS).document(metric['post_id']).get()
                if post_doc.exists:
                    post_data = post_doc.to_dict()
                    post_data['id'] = post_doc.id
                    popular_posts.append(post_data)
            
            return popular_posts
        except Exception as e:
            self.logger.error(f"Popüler postlar alınırken hata: {str(e)}")
            return []

    def get_random_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Rastgele postları getirir"""
        try:
            posts = self.get_collection(COLLECTION_POSTS)
            random.shuffle(posts)
            return posts[:limit]
        except Exception as e:
            raise Exception(f"Rastgele postlar alınırken hata: {str(e)}")

    def add_post(self, post_data: Dict) -> str:
        """Yeni post ekle"""
        try:
            post_data['created_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            doc_ref = self.db.collection(COLLECTION_POSTS).document()
            doc_ref.set(post_data)
            return doc_ref.id
        except Exception as e:
            self.logger.error(f"Post eklenirken hata: {str(e)}")
            return None

    def delete_post(self, post_id: str) -> bool:
        """Belirtilen ID'ye sahip postu siler"""
        try:
            self.db.collection(COLLECTION_POSTS).document(post_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Post silinirken hata: {str(e)}")
            return False

    def update_post_metrics(self, post_id: str, metrics: Dict) -> bool:
        """Post metriklerini günceller"""
        try:
            data = {
                **metrics,
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            
            doc_ref = self.db.collection(COLLECTION_POST_METRICS).document(post_id)
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Post metrikleri güncellenirken hata: {str(e)}")
            return False

    def get_recent_content(self, days: int = 7) -> List[Dict]:
        """Son günlerin içeriklerini getirir"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days))
            posts = []
            
            docs = self.db.collection(COLLECTION_POSTS)\
                .where("created_at", ">=", cutoff_date)\
                .order_by("created_at")\
                .stream()
            
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Son içerikleri getirme hatası: {str(e)}")
            return []

    def get_popular_content(self, days: int = 30) -> List[Dict]:
        """Popüler içerikleri getirir"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days))
            
            # Post metriklerini al
            metrics = []
            docs = self.db.collection(COLLECTION_POST_METRICS)\
                .where("updated_at", ">=", cutoff_date)\
                .stream()
            
            for doc in docs:
                metric_data = doc.to_dict()
                metric_data['id'] = doc.id
                metrics.append(metric_data)
            
            # Metrikleri etkileşim sayısına göre sırala
            sorted_metrics = sorted(metrics, key=lambda x: x.get('interaction_count', 0), reverse=True)
            
            # En popüler postları getir
            popular_posts = []
            for metric in sorted_metrics[:100]:
                post_doc = self.db.collection(COLLECTION_POSTS).document(metric['post_id']).get()
                if post_doc.exists:
                    post_data = post_doc.to_dict()
                    post_data['id'] = post_doc.id
                    popular_posts.append(post_data)
            
            return popular_posts
        except Exception as e:
            self.logger.error(f"Popüler içerikleri getirme hatası: {str(e)}")
            return []

    def get_post_by_id(self, post_id):
        try:
            post_ref = self.db.collection(COLLECTION_POSTS).document(post_id)
            post = post_ref.get()
            return post.to_dict() if post.exists else None
        except Exception as e:
            print(f"İçerik getirilirken hata: {str(e)}")
            return None 