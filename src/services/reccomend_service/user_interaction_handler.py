from typing import Dict, List, Any
import logging
from services.pattern_manager import PatternManager

class UserInteractionHandler:
    def __init__(self, pattern_manager: PatternManager):
        self.logger = logging.getLogger(__name__)
        self.pattern_manager = pattern_manager

    async def process_user_interaction(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        firebase_service
    ) -> None:
        """Kullanıcı etkileşimini işler ve pattern'i günceller"""
        try:
            # Etkileşim tipine göre ağırlık belirle
            weight = self.pattern_manager._get_interaction_weight(interaction_data.get('interaction_type'))
            
            # Etkileşimi kaydet
            await firebase_service.log_interaction(
                user_id=user_id,
                content_id=interaction_data.get('content_id'),
                interaction_type=interaction_data.get('interaction_type'),
                emotion=interaction_data.get('emotion'),
                weight=weight,
                is_ad=interaction_data.get('is_ad', False)
            )
            
        except Exception as e:
            self.logger.error(f"Etkileşim işleme hatası: {str(e)}")
            raise

    async def get_user_pattern(
        self,
        user_id: str,
        firebase_service,
        interactions: List[Dict]
    ) -> Dict[str, float]:
        """Kullanıcı pattern'ini getirir veya oluşturur"""
        try:
            # Pattern'i al
            pattern = await firebase_service.get_user_pattern(user_id)
            
            # Pattern yoksa veya etkileşim sayısı azsa, yeni pattern oluştur
            if not pattern or len(interactions) < 20:
                if interactions:
                    pattern = self.pattern_manager._create_pattern_from_interactions(interactions)
                    await firebase_service.update_user_pattern(user_id, pattern)
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"Pattern getirme hatası: {str(e)}")
            return {} 