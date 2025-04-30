from typing import Dict, List, Any
import logging

class AdManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def _get_available_ads(self, firebase_service) -> List[Dict]:
        """Mevcut reklamları getirir"""
        # Son 7 günün reklamlarını al
        recent_ads = await firebase_service.get_recent_ads(days=7)
        
        if len(recent_ads) >= 3:  # En az 3 reklam
            return recent_ads
            
        # Yeterli yeni reklam yoksa, yüksek CTR'lı reklamları ekle
        high_ctr_ads = await firebase_service.get_high_ctr_ads()
        
        # Yeni reklamları önceliklendir
        combined_ads = recent_ads + [
            ad for ad in high_ctr_ads 
            if ad not in recent_ads
        ]
        
        return combined_ads[:3]  # En fazla 3 reklam

    def _merge_content_and_ads(
        self,
        content: List[Dict[str, Any]],
        ads: List[Dict[str, Any]],
        ad_frequency: int
    ) -> List[Dict[str, Any]]:
        """İçerik ve reklamları birleştirir"""
        merged = []
        ad_index = 0
        
        for i, item in enumerate(content):
            merged.append(item)
            
            # Her ad_frequency içerikte bir reklam ekle
            if (i + 1) % ad_frequency == 0 and ad_index < len(ads):
                merged.append(ads[ad_index])
                ad_index += 1
        
        return merged

    async def _get_ad_recommendations(
        self, 
        user_pattern: Dict[str, Any],
        firebase_service,
        content_scorer
    ) -> List[Dict[str, Any]]:
        """Kullanıcı pattern'ine göre reklam önerileri oluşturur"""
        try:
            all_ads = await firebase_service.get_all_ads()
            
            # Reklamları puanla
            scored_ads = []
            for ad in all_ads:
                relevance = content_scorer.calculate_relevance_score(ad, [], user_pattern)
                scored_ads.append((ad, relevance))
            
            # Puanlara göre sırala
            scored_ads.sort(key=lambda x: x[1], reverse=True)
            
            # En uygun reklamları seç
            return [ad for ad, _ in scored_ads[:5]]  # İlk 5 en uygun reklam
            
        except Exception as e:
            raise Exception(f"Reklam önerileri oluşturulurken hata: {str(e)}") 