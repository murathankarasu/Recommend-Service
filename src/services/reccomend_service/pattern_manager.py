from typing import Dict, List
import logging
from config import EMOTION_CATEGORIES

class PatternManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _create_pattern_from_interactions(self, interactions: List[Dict]) -> Dict[str, float]:
        """Mevcut etkileşimlere göre pattern oluşturur"""
        pattern = {emotion: 0.0 for emotion in EMOTION_CATEGORIES}
        total_weight = 0.0

        for interaction in interactions:
            emotion = interaction.get('emotion')
            if emotion in EMOTION_CATEGORIES:
                weight = self._get_interaction_weight(interaction.get('interactionType', 'view'))
                pattern[emotion] += weight
                total_weight += weight

        # Normalize et
        if total_weight > 0:
            for emotion in pattern:
                pattern[emotion] /= total_weight

        return pattern

    def _get_interaction_weight(self, interaction_type: str) -> float:
        """Etkileşim tipine göre ağırlık döndürür"""
        weights = {
            'like': 0.5,
            'comment': 1.0,
            'create': 1.5,
            'share': 1.2
        }
        return weights.get(interaction_type, 0.3)  # Varsayılan ağırlık

    def _check_emotion_continuity(self, interactions: List[Dict]) -> bool:
        """Kullanıcının tek duyguda takılıp kalmadığını kontrol eder"""
        if not interactions:
            return False

        # Son 10 etkileşimi kontrol et
        recent_interactions = sorted(
            interactions, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )[:10]

        if len(recent_interactions) < 10:
            return False

        # Baskın duyguyu bul
        emotions = [i['emotion'] for i in recent_interactions]
        dominant_emotion = max(set(emotions), key=emotions.count)

        # Eğer son 10 etkileşimin çoğu aynı duygudaysa
        return emotions.count(dominant_emotion) >= 8 