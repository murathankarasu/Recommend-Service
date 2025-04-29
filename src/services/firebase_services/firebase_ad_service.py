from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .firebase_base import FirebaseBase
from config import COLLECTION_ADS, COLLECTION_AD_METRICS
import logging

class FirebaseAdService(FirebaseBase):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    async def get_all_ads(self) -> List[Dict]:
        """Tüm reklamları getirir"""
        try:
            ads = []
            docs = self.db.collection(COLLECTION_ADS).stream()
            
            for doc in docs:
                ad_data = doc.to_dict()
                ad_data['id'] = doc.id
                ads.append(ad_data)
            
            return ads
        except Exception as e:
            self.logger.error(f"Reklamlar alınırken hata: {str(e)}")
            return []

    async def get_active_ads(self) -> List[Dict]:
        """Aktif reklamları getirir"""
        try:
            ads = []
            docs = self.db.collection(COLLECTION_ADS)\
                .where("is_active", "==", True)\
                .stream()
            
            for doc in docs:
                ad_data = doc.to_dict()
                ad_data['id'] = doc.id
                ads.append(ad_data)
            
            return ads
        except Exception as e:
            self.logger.error(f"Aktif reklamlar alınırken hata: {str(e)}")
            return []

    async def get_ads_by_category(self, category: str) -> List[Dict]:
        """Kategoriye göre reklamları getirir"""
        try:
            ads = []
            docs = self.db.collection(COLLECTION_ADS)\
                .where("category", "==", category)\
                .where("is_active", "==", True)\
                .stream()
            
            for doc in docs:
                ad_data = doc.to_dict()
                ad_data['id'] = doc.id
                ads.append(ad_data)
            
            return ads
        except Exception as e:
            self.logger.error(f"Kategori bazlı reklamlar alınırken hata: {str(e)}")
            return []

    async def add_ad(self, ad_data: Dict) -> str:
        """Yeni reklam ekler"""
        try:
            ad_data['created_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            ad_data['is_active'] = True
            
            doc_ref = self.db.collection(COLLECTION_ADS).document()
            doc_ref.set(ad_data)
            
            # Reklam metriklerini başlat
            await self._initialize_ad_metrics(doc_ref.id)
            
            return doc_ref.id
        except Exception as e:
            self.logger.error(f"Reklam eklenirken hata: {str(e)}")
            return None

    async def update_ad(self, ad_id: str, ad_data: Dict) -> bool:
        """Reklamı günceller"""
        try:
            ad_data['updated_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            doc_ref = self.db.collection(COLLECTION_ADS).document(ad_id)
            doc_ref.set(ad_data, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Reklam güncellenirken hata: {str(e)}")
            return False

    async def delete_ad(self, ad_id: str) -> bool:
        """Reklamı siler"""
        try:
            self.db.collection(COLLECTION_ADS).document(ad_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Reklam silinirken hata: {str(e)}")
            return False

    async def update_ad_metrics(self, ad_id: str, metrics: Dict) -> bool:
        """Reklam metriklerini günceller"""
        try:
            data = {
                **metrics,
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            
            doc_ref = self.db.collection(COLLECTION_AD_METRICS).document(ad_id)
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Reklam metrikleri güncellenirken hata: {str(e)}")
            return False

    async def get_ad_metrics(self, ad_id: str) -> Optional[Dict]:
        """Reklam metriklerini getirir"""
        try:
            doc = self.db.collection(COLLECTION_AD_METRICS).document(ad_id).get()
            if doc.exists:
                metrics = doc.to_dict()
                metrics['id'] = doc.id
                return metrics
            return None
        except Exception as e:
            self.logger.error(f"Reklam metrikleri alınırken hata: {str(e)}")
            return None

    async def _initialize_ad_metrics(self, ad_id: str) -> None:
        """Reklam metriklerini başlatır"""
        try:
            initial_metrics = {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "ctr": 0.0,
                "conversion_rate": 0.0,
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            
            doc_ref = self.db.collection(COLLECTION_AD_METRICS).document(ad_id)
            doc_ref.set(initial_metrics)
        except Exception as e:
            self.logger.error(f"Reklam metrikleri başlatılırken hata: {str(e)}")

    async def get_performance_report(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Reklam performans raporunu getirir"""
        try:
            metrics = []
            docs = self.db.collection(COLLECTION_AD_METRICS)\
                .where("updated_at", ">=", start_date)\
                .where("updated_at", "<=", end_date)\
                .stream()
            
            for doc in docs:
                metric_data = doc.to_dict()
                metric_data['id'] = doc.id
                
                # İlgili reklam bilgilerini getir
                ad_doc = self.db.collection(COLLECTION_ADS).document(doc.id).get()
                if ad_doc.exists:
                    ad_data = ad_doc.to_dict()
                    metric_data['ad_info'] = {
                        'title': ad_data.get('title'),
                        'category': ad_data.get('category'),
                        'is_active': ad_data.get('is_active')
                    }
                
                metrics.append(metric_data)
            
            return metrics
        except Exception as e:
            self.logger.error(f"Performans raporu alınırken hata: {str(e)}")
            return [] 