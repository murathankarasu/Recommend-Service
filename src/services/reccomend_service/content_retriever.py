from typing import Dict, List, Any
import logging

class ContentRetriever:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.RECENT_DAYS = 7  # Son 7 gün
        self.POPULAR_DAYS = 30  # Son 30 gün

    async def get_available_content(self, firebase_service) -> List[Dict[str, Any]]:
        """Mevcut içerikleri getirir"""
        try:
            # Son 7 günün içeriklerini al
            recent_content = firebase_service.get_recent_content(
                days=self.RECENT_DAYS
            )
            
            if len(recent_content) >= 10:
                return recent_content
                
            # Yeterli yeni içerik yoksa, son 30 günün popüler içeriklerini ekle
            popular_content = firebase_service.get_popular_content(
                days=self.POPULAR_DAYS
            )
            
            # Yeni içerikleri önceliklendir
            combined_content = recent_content + [
                content for content in popular_content 
                if content not in recent_content
            ]
            
            return combined_content[:10]  # En fazla 10 içerik
            
        except Exception as e:
            self.logger.error(f"İçerik getirme hatası: {str(e)}")
            return []

    async def get_recent_and_popular_content(
        self,
        firebase_service,
        recent_days: int = 7,
        popular_days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Son ve popüler içerikleri getirir"""
        try:
            recent_content = firebase_service.get_recent_content(days=recent_days)
            popular_content = firebase_service.get_popular_content(days=popular_days)
            
            return {
                'recent': recent_content,
                'popular': popular_content
            }
            
        except Exception as e:
            self.logger.error(f"İçerik getirme hatası: {str(e)}")
            return {'recent': [], 'popular': []} 