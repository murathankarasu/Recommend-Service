import logging
import random
from typing import Dict, List, Any
from datetime import datetime
from config.config import (
    CONTENT_QUALITY_METRICS,
    TIME_BASED_OPTIMIZATION,
    DIVERSITY_CONTROLS,
    INTERACTION_QUALITY_METRICS,
    INTERACTION_TYPE_WEIGHTS
)

logger = logging.getLogger(__name__)

class ContentRecommender:
    def __init__(self):
        self.content_engagement = {}  # İçerik bazlı etkileşim istatistikleri
        self.interaction_weights = INTERACTION_TYPE_WEIGHTS

    def calculate_content_relevance(self, content: Dict[str, Any], user_pattern: Dict[str, float]) -> float:
        """İçeriğin kullanıcı desenine uygunluğunu hesaplar."""
        try:
            content_emotion = content.get('emotion')
            if content_emotion not in user_pattern:
                return 0.0
        
            base_relevance = user_pattern.get(content_emotion, 0.0)
            
            content_id = content.get('id')
            if content_id in self.content_engagement:
                engagement_score = self._calculate_engagement_score(content_id)
                base_relevance *= (1.0 + engagement_score)

            return min(1.0, max(0.0, base_relevance))

        except Exception as e:
            logger.error(f"İçerik uygunluğu hesaplanırken hata: {str(e)}")
            return 0.0

    def _calculate_engagement_score(self, content_id: str) -> float:
        """İçerik etkileşim skorunu hesaplar."""
        engagement = self.content_engagement.get(content_id, {})
        total_engagements = sum(engagement.values())
        if total_engagements == 0:
            return 0.0
        
        weighted_score = sum(
            count * self.interaction_weights.get(interaction_type, 0.1)
            for interaction_type, count in engagement.items()
        )
        
        return min(1.0, weighted_score / total_engagements)

    def _calculate_content_quality_score(self, content: Dict[str, Any]) -> float:
        """İçerik kalite skorunu hesaplar"""
        score = 0
        for metric, weight in CONTENT_QUALITY_METRICS.items():
            if metric == 'engagement_rate':
                score += weight * (content.get('likes', 0) + content.get('comments', 0)) / max(content.get('views', 1), 1)
            elif metric == 'freshness':
                created_at = content.get('created_at', datetime.now())
                dt = None
                if isinstance(created_at, str):
                    try:
                        dt = datetime.fromisoformat(created_at)
                    except Exception:
                        try:
                            dt = datetime.strptime(created_at, "%B %d, %Y at %I:%M:%S %p UTC+3")
                        except Exception:
                            dt = datetime.now()
                else:
                    dt = created_at
                content_age = (datetime.now() - dt).days
                score += weight * (1 / (1 + content_age))
            elif metric == 'user_reputation':
                score += weight * content.get('user_reputation', 0.5)
            elif metric == 'content_length':
                content_length = len(content.get('content', ''))
                score += weight * min(content_length / 1000, 1)
        return score

    def _apply_time_based_optimization(self, score: float, timestamp: datetime) -> float:
        """Zaman bazlı optimizasyon uygular"""
        hour = timestamp.hour
        if TIME_BASED_OPTIMIZATION['peak_hours']['start'] <= hour <= TIME_BASED_OPTIMIZATION['peak_hours']['end']:
            return score * TIME_BASED_OPTIMIZATION['peak_hours']['weight_multiplier']
        return score * TIME_BASED_OPTIMIZATION['off_peak_hours']['weight_multiplier']

    def _ensure_content_diversity(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """İçerik çeşitliliğini sağlar"""
        if len(recommendations) <= DIVERSITY_CONTROLS['max_similar_content']:
            return recommendations
        
        diverse_recommendations = []
        topic_counts = {}
        
        for rec in recommendations:
            topic = rec.get('topic', 'general')
            if topic_counts.get(topic, 0) < DIVERSITY_CONTROLS['max_similar_content']:
                diverse_recommendations.append(rec)
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
        return diverse_recommendations

    def _calculate_interaction_quality(self, interaction: Dict[str, Any]) -> float:
        """Etkileşim kalite skorunu hesaplar"""
        score = 0
        for metric, weight in INTERACTION_QUALITY_METRICS.items():
            if metric == 'duration':
                score += weight * min(interaction.get('duration', 0) / 60, 1)
            elif metric == 'depth':
                score += weight * len(interaction.get('details', {}))
            elif metric == 'frequency':
                score += weight * min(interaction.get('frequency', 0) / 10, 1)
            elif metric == 'recency':
                recency = (datetime.now() - interaction.get('timestamp', datetime.now())).days
                score += weight * (1 / (1 + recency))
        return score

    def update_content_engagement(self, content_id: str, interaction_type: str):
        """İçerik etkileşim istatistiklerini günceller."""
        if content_id not in self.content_engagement:
            self.content_engagement[content_id] = {}
        
        self.content_engagement[content_id][interaction_type] = (
            self.content_engagement[content_id].get(interaction_type, 0) + 1
        )

    def get_content_mix(self, contents: List[Dict], emotion_pattern: Dict[str, float], limit: int = 20) -> List[Dict]:
        """Kullanıcı duygu desenine göre içerik karışımı oluşturur."""
        # İçeriklere uygunluk skoru ata
        scored_contents = [
            (content, self.calculate_content_relevance(content, emotion_pattern))
            for content in contents
        ]
        # Skora göre sırala
        scored_contents.sort(key=lambda x: x[1], reverse=True)
        # Sadece içerik objelerini al, ilk 'limit' kadar
        recommendations = [content for content, score in scored_contents[:limit]]
        # Çeşitlilik uygula
        recommendations = self._ensure_content_diversity(recommendations)
        return recommendations 