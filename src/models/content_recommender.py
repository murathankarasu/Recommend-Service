import logging
import random
from typing import Dict, List, Any
from datetime import datetime, timezone
from config.config import (
    CONTENT_QUALITY_METRICS,
    TIME_BASED_OPTIMIZATION,
    DIVERSITY_CONTROLS,
    INTERACTION_QUALITY_METRICS,
    INTERACTION_TYPE_WEIGHTS,
    EMOTION_CATEGORIES
)
from services.reccomend_service.shuffle_utils import shuffle_same_score
from services.reccomend_service.date_utils import parse_timestamp
from services.reccomend_service.cold_start_utils import get_cold_start_content

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

    def get_content_mix(self, contents: List[Dict], emotion_pattern: Dict[str, float], limit: int = 20, shown_post_ids: List[Any] = None, repeat_ratio: float = 0.2, timeout_sec: int = 3) -> List[Dict]:
        """
        Kullanıcıya önerilecek içerik karışımını oluşturur:
        - Öncelik: Son 1 haftanın unseen içerikleri (duygu patternine uygun hikaye)
        - Eğer 1 haftalık unseen içerik yetersizse, tüm unseen içeriklerden doldur
        - Eğer unseen içerik yetersizse, kalan slotları cold start ile doldur
        - Cold start da yetersizse, tekrarlarla doldur
        - Her duygudan en az 1 içerik eklemeye çalışır
        - Pattern ve çeşitlilik kurallarına uyar
        - Timeout ile işlem süresi sınırlandırılır
        """
        import time
        from collections import defaultdict
        import heapq
        from datetime import timedelta
        start_time = time.time()
        logger.info(f"[get_content_mix] Başladı. İçerik: {len(contents)}, shown_post_ids: {len(shown_post_ids) if shown_post_ids else 0}, limit: {limit}")
        if shown_post_ids is None:
            shown_post_ids = []
        # 1. Son 1 haftanın unseen içeriklerini filtrele
        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=7)
        def safe_parse_timestamp(ts):
            dt = parse_timestamp(ts)
            if dt is None:
                return datetime(1970, 1, 1, tzinfo=timezone.utc)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        unseen_contents = [c for c in contents if c.get('id') not in shown_post_ids and safe_parse_timestamp(c.get('timestamp')) >= one_week_ago]
        logger.info(f"[get_content_mix] Son 1 haftanın unseen içerikleri: {len(unseen_contents)}")
        # Eğer yeterli değilse, tüm unseen içerikleri ekle
        if len(unseen_contents) < limit:
            extra_unseen = [c for c in contents if c.get('id') not in shown_post_ids and c not in unseen_contents]
            unseen_contents += extra_unseen
            logger.info(f"[get_content_mix] Tüm unseen içerikler eklendi: {len(unseen_contents)}")
        # 2. Eğer unseen içerik yetersizse, kalan slotları cold start ile doldur
        selected = []
        if len(unseen_contents) < limit:
            logger.info(f"[get_content_mix] Cold start içerik ekleniyor. Eksik slot: {limit - len(unseen_contents)}")
            cold_start_needed = limit - len(unseen_contents)
            cold_start_contents = get_cold_start_content(
                contents,  # shown_post_ids ile filtreleme YOK!
                list(EMOTION_CATEGORIES.values()),
                cold_start_needed
            )
            unseen_contents += cold_start_contents
            logger.info(f"[get_content_mix] Cold start sonrası unseen_contents: {len(unseen_contents)}")
            # Hala eksik varsa, tekrarları ekle (en son çare)
            if len(unseen_contents) < limit:
                seen_contents = [c for c in contents if c.get('id') in shown_post_ids]
                random.shuffle(seen_contents)
                unseen_contents += seen_contents[:limit - len(unseen_contents)]
                logger.info(f"[get_content_mix] Tekrar içerikler eklendi. unseen_contents: {len(unseen_contents)}")
        # 3. İçerikleri duygulara göre grupla
        emotion_to_contents = defaultdict(list)
        for content in unseen_contents:
            emotion = content.get('emotion')
            if emotion:
                emotion_to_contents[emotion].append(content)
        logger.info(f"[get_content_mix] emotion_to_contents oluşturuldu. Duygu sayısı: {len(emotion_to_contents)}")
        # 4. Her duygudan en az 1 içerik (varsa) ekle, yakın tarihli olanları öne al
        for emotion, content_list in emotion_to_contents.items():
            sorted_list = sorted(content_list, key=lambda c: safe_parse_timestamp(c.get('timestamp')), reverse=True)
            if sorted_list:
                selected.append(sorted_list[0])
        logger.info(f"[get_content_mix] Her duygudan içerik eklendi. selected: {len(selected)}")
        # 5. Pattern oranına göre kalan slotları doldur
        remaining_limit = limit - len(selected)
        if remaining_limit > 0:
            logger.info(f"[get_content_mix] Pattern oranına göre slot dolduruluyor. Kalan: {remaining_limit}")
            scored_contents = []
            for content in unseen_contents:
                if time.time() - start_time > timeout_sec:
                    logger.warning(f"[get_content_mix] TIMEOUT! Süre aşıldı. Şu ana kadar seçilen içerik: {len(selected)}")
                    break
                emotion = content.get('emotion')
                if not emotion:
                    continue
                pattern_score = emotion_pattern.get(emotion, 0.0)
                relevance = self.calculate_content_relevance(content, emotion_pattern)
                timestamp = content.get('timestamp')
                recency_score = 0.2
                try:
                    dt = parse_timestamp(timestamp)
                    if dt:
                        days_ago = (now - dt).days
                        if days_ago <= 7:
                            recency_score = 1.0
                        elif days_ago <= 30:
                            recency_score = 0.5
                except Exception:
                    pass
                total_score = pattern_score * 0.5 + relevance * 0.3 + recency_score * 0.2
                scored_contents.append((total_score, content))
            selected_ids = set(c['id'] for c in selected)
            filtered = [(score, c) for score, c in scored_contents if c['id'] not in selected_ids]
            shuffled = shuffle_same_score(filtered)
            selected += shuffled[:remaining_limit]
            logger.info(f"[get_content_mix] Pattern sonrası selected: {len(selected)}")
        # 6. Eğer tek bir duygu çok baskınsa, diğer duygulardan da ekle (çeşitlilik)
        emotion_counts = defaultdict(int)
        for c in selected:
            emotion_counts[c.get('emotion')] += 1
        if emotion_counts:
            max_emotion = max(emotion_counts, key=emotion_counts.get)
            if emotion_counts[max_emotion] > limit * 0.7:
                logger.info(f"[get_content_mix] Çeşitlilik için ek içerik ekleniyor. Baskın duygu: {max_emotion}")
                for emotion, content_list in emotion_to_contents.items():
                    if emotion == max_emotion:
                        continue
                    for content in content_list:
                        if content not in selected:
                            selected.append(content)
                            if len(selected) >= limit:
                                break
                    if len(selected) >= limit:
                        break
        logger.info(f"[get_content_mix] TAMAMLANDI. Sonuç: {len(selected[:limit])} içerik, Toplam süre: {time.time() - start_time:.2f} sn")
        return selected[:limit] 