from datetime import datetime, timedelta
from typing import Dict, List, Optional
from typing import Any
from .firebase_base import FirebaseBase
from config import COLLECTION_POSTS, COLLECTION_POST_METRICS
import logging

class FirebasePostService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_all_posts(self) -> List[Dict]:
        """Tüm postları getirir"""
        try:
            posts = []
            docs = self.db.collection(COLLECTION_POSTS).stream()
            
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Postlar alınırken hata: {str(e)}")
            return []

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