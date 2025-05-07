import logging
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone
from config.config import (
    CONTENT_QUALITY_METRICS,
    TIME_BASED_OPTIMIZATION,
    DIVERSITY_CONTROLS,
    INTERACTION_QUALITY_METRICS,
    INTERACTION_TYPE_WEIGHTS,
    EMOTION_CATEGORIES,
    OPPOSITE_EMOTIONS,
    EMOTION_TRANSITION_MATRIX,
    KEYWORD_MATCH_WEIGHT
)
from services.reccomend_service.shuffle_utils import shuffle_same_score
from services.reccomend_service.date_utils import parse_timestamp
from services.reccomend_service.cold_start_utils import get_cold_start_content

logger = logging.getLogger(__name__)

class ContentRecommender:
    def __init__(self):
        self.content_engagement = {}  # İçerik bazlı etkileşim istatistikleri
        self.interaction_weights = INTERACTION_TYPE_WEIGHTS
        self.keyword_match_weight = KEYWORD_MATCH_WEIGHT  # Keyword eşleşme ağırlığı

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

            # Keyword eşleşme skorunu ekle
            keyword_score = self._calculate_keyword_match_score(content)
            base_relevance = base_relevance * (1 - self.keyword_match_weight) + keyword_score * self.keyword_match_weight

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

    def _find_next_emotion(self,
                           from_emotion: str,
                           personalized_transitions: Dict[Tuple[str, str], int],
                           exclude_emotion: Optional[str] = None) -> Optional[str]:
        """Finds the most frequent next emotion based on personalized data, with fallback."""
        candidates = []
        for (f_emo, t_emo), count in personalized_transitions.items():
            if f_emo == from_emotion and t_emo != exclude_emotion:
                candidates.append((count, t_emo))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1] # Return the emotion with the highest count
        else:
            # Fallback to generic matrix if no personalized data for this transition
            generic_transitions = EMOTION_TRANSITION_MATRIX.get(from_emotion, {})
            if not generic_transitions:
                return None
            # Sort generic transitions by probability
            sorted_generic = sorted(generic_transitions.items(), key=lambda item: item[1], reverse=True)
            for emo, prob in sorted_generic:
                 if emo != from_emotion and emo != exclude_emotion: # Avoid self and excluded
                      return emo
            # If only self-transition or excluded exists in generic, return None or the first one?
            return sorted_generic[0][0] if sorted_generic else None

    def get_content_mix(
        self,
        contents: List[Dict],
        emotion_pattern: Dict[str, float],
        limit: int = 20,
        shown_post_ids: List[Any] = None,
        current_emotion: Optional[str] = None,
        personalized_transitions: Dict[Tuple[str, str], int] = None,
        repeat_ratio: float = 0.2,
        timeout_sec: int = 3
    ) -> Tuple[List[Dict], Optional[int]]:
        """
        Creates a detailed story flow based on personalized transitions.
        - Plans a 3-step emotional journey (Current -> Next1 -> Next2) using personalized data.
        - Selects content for each step.
        - Identifies the peak moment based on the most frequent personalized transition.
        - Fills remaining slots based on relevance and diversity.
        """
        import time
        from collections import defaultdict
        from datetime import timedelta
        start_time = time.time()

        if shown_post_ids is None: shown_post_ids = []
        if personalized_transitions is None: personalized_transitions = {}

        logger.info(f"[get_content_mix] DETAILED FLOW. Current: {current_emotion}, Personalized Transitions: {len(personalized_transitions)}")

        # 1. Prepare content pools (as before)
        now = datetime.now(timezone.utc)
        def safe_parse_timestamp(ts):
            dt = parse_timestamp(ts)
            if dt is None: return datetime(1970, 1, 1, tzinfo=timezone.utc)
            if dt.tzinfo is None: return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        recent_unseen = sorted([c for c in contents if c.get('id') not in shown_post_ids and safe_parse_timestamp(c.get('timestamp')) >= now - timedelta(days=7)], key=lambda c: safe_parse_timestamp(c.get('timestamp')), reverse=True)
        other_unseen = [c for c in contents if c.get('id') not in shown_post_ids and c not in recent_unseen]
        all_unseen_pool = recent_unseen + other_unseen
        random.shuffle(all_unseen_pool)

        # 2. Plan the Detailed Story Arc (Current -> Next1 -> Next2)
        story_arc_emotions = []
        next_emotion_1 = None
        next_emotion_2 = None

        if current_emotion:
            story_arc_emotions.append(current_emotion)
            # Find Next1
            next_emotion_1 = self._find_next_emotion(current_emotion, personalized_transitions)
            if next_emotion_1:
                story_arc_emotions.append(next_emotion_1)
                # Find Next2 (try not to repeat current or next1)
                next_emotion_2 = self._find_next_emotion(next_emotion_1, personalized_transitions, exclude_emotion=current_emotion)
                # If Next2 repeats Next1, try again excluding both
                if next_emotion_2 == next_emotion_1:
                     next_emotion_2 = self._find_next_emotion(next_emotion_1, personalized_transitions, exclude_emotion=[current_emotion, next_emotion_1])

                if next_emotion_2:
                    story_arc_emotions.append(next_emotion_2)

        logger.info(f"[get_content_mix] Planned story arc: {story_arc_emotions}")

        # 3. Select Content for the Story Arc
        selected_mix: List[Dict] = []
        used_content_ids = set()
        arc_content_indices = {} # Store index of content for each arc emotion

        for i, arc_emotion in enumerate(story_arc_emotions):
            found_content = False
            # Önce o duygudaki içerikler içinden, keyword eşleşenleri bul
            emotion_candidates = [c for c in recent_unseen + other_unseen if c.get('emotion') == arc_emotion and c.get('id') not in used_content_ids]
            if emotion_candidates:
                # Kullanıcı keywordleriyle eşleşenleri öne al
                user_keywords = self._get_user_recent_keywords()
                keyword_matched = [c for c in emotion_candidates if user_keywords and set(c.get('keywords', [])) & user_keywords]
                if keyword_matched:
                    selected = random.choice(keyword_matched)
                else:
                    selected = random.choice(emotion_candidates)
                selected_mix.append(selected)
                used_content_ids.add(selected['id'])
                arc_content_indices[arc_emotion] = len(selected_mix) - 1
                logger.info(f"[get_content_mix] Added arc content [{i+1}/{len(story_arc_emotions)}]: {arc_emotion}")
                found_content = True
            if not found_content:
                logger.warning(f"[get_content_mix] Could not find unseen content for arc step: {arc_emotion}. Stopping arc sequence here.")
                story_arc_emotions = story_arc_emotions[:i]
                break

        # 4. Determine the Peak Moment Index
        peak_moment_index: Optional[int] = None
        if len(story_arc_emotions) >= 2: # Need at least one transition
            transition1 = (story_arc_emotions[0], story_arc_emotions[1])
            transition1_count = personalized_transitions.get(transition1, 0)
            peak_transition = transition1
            highest_count = transition1_count

            if len(story_arc_emotions) >= 3:
                transition2 = (story_arc_emotions[1], story_arc_emotions[2])
                transition2_count = personalized_transitions.get(transition2, 0)
                if transition2_count > highest_count:
                    peak_transition = transition2
                    highest_count = transition2_count
                # If counts are equal, maybe prefer the one leading to a more positive emotion?
                # Or just keep the first one (transition1) for simplicity if counts are equal.

            # Set peak index *after* the content of the emotion reached by the peak transition
            peak_emotion_reached = peak_transition[1]
            if peak_emotion_reached in arc_content_indices:
                peak_moment_index = arc_content_indices[peak_emotion_reached] + 1
                logger.info(f"[get_content_mix] Peak determined after emotion '{peak_emotion_reached}' (Transition: {peak_transition} Count: {highest_count}). Peak index: {peak_moment_index}")
            else: # Fallback if something went wrong with indexing
                 if len(selected_mix) >= 1: peak_moment_index = 1
                 if len(selected_mix) >= 2: peak_moment_index = 2 # Default to after first or second item
                 logger.warning("[get_content_mix] Could not map peak emotion to index, using default peak index.")
        elif len(selected_mix) > 0: # If only one arc item, peak is after it
             peak_moment_index = 1
             logger.info("[get_content_mix] Only one arc item, setting peak index to 1.")


        # 5. Fill Remaining Slots (similar logic as before, maybe add bonus for arc emotions)
        remaining_limit = limit - len(selected_mix)
        if remaining_limit > 0:
            logger.info(f"[get_content_mix] Filling remaining {remaining_limit} slots.")
            remaining_pool = [c for c in all_unseen_pool if c.get('id') not in used_content_ids]
            scored_contents = []
            for content in remaining_pool:
                if time.time() - start_time > timeout_sec:
                    logger.warning(f"[get_content_mix] TIMEOUT during filling remaining slots!")
                    break

                emotion = content.get('emotion')
                if not emotion: continue

                pattern_score = emotion_pattern.get(emotion, 0.0)
                relevance = self.calculate_content_relevance(content, emotion_pattern)
                recency_score = 0.2
                try:
                    dt = parse_timestamp(content.get('timestamp'))
                    if dt: days_ago = (now - dt).days
                    else: days_ago = 999
                    if days_ago <= 1: recency_score = 1.0
                    elif days_ago <= 7: recency_score = 0.7
                    elif days_ago <= 30: recency_score = 0.4
                except Exception: pass

                # Bonus if emotion is part of the planned (even if not achieved) arc
                story_bonus = 0.05 if emotion in story_arc_emotions else 0.0

                total_score = pattern_score * 0.4 + relevance * 0.3 + recency_score * 0.15 + story_bonus * 0.1
                scored_contents.append((total_score, content))

            scored_contents.sort(key=lambda x: x[0], reverse=True)
            added_count = 0
            for score, content in scored_contents:
                if len(selected_mix) >= limit: break
                if content.get('id') not in used_content_ids:
                    selected_mix.append(content)
                    used_content_ids.add(content['id'])
                    added_count += 1
            logger.info(f"[get_content_mix] Added {added_count} more items based on score.")

        # 6. Fallback Fill (if still under limit)
        if len(selected_mix) < limit:
            logger.warning(f"[get_content_mix] Still under limit. Falling back to seen/cold start pool.")
            needed = limit - len(selected_mix)
            fallback_pool = [c for c in contents if c.get('id') not in used_content_ids] # Broadest pool
            random.shuffle(fallback_pool)
            fill_count = 0
            for content in fallback_pool:
                 if len(selected_mix) >= limit: break
                 if content.get('id') not in used_content_ids:
                      selected_mix.append(content)
                      used_content_ids.add(content['id'])
                      fill_count+=1
            logger.info(f"[get_content_mix] Added {fill_count} items from fallback pool.")

        # 7. Final Shuffle (Maybe only shuffle *after* the planned arc?)
        # Shuffle items after the planned arc sequence to maintain the initial story flow
        arc_len = len(story_arc_emotions)
        if arc_len < len(selected_mix):
            to_shuffle = selected_mix[arc_len:]
            random.shuffle(to_shuffle)
            selected_mix = selected_mix[:arc_len] + to_shuffle
            logger.info(f"[get_content_mix] Shuffled content after the initial {arc_len} arc items.")

        logger.info(f"[get_content_mix] DETAILED FLOW Tamamlandı. Öneri: {len(selected_mix)}, Peak index: {peak_moment_index}")
        return selected_mix[:limit], peak_moment_index 

    def _calculate_keyword_match_score(self, content: Dict[str, Any]) -> float:
        """İçeriğin keyword eşleşme skorunu hesaplar."""
        try:
            content_keywords = set(content.get('keywords', []))
            if not content_keywords:
                return 0.0

            # Kullanıcının son etkileşimlerindeki keywordleri al
            user_keywords = self._get_user_recent_keywords()
            if not user_keywords:
                return 0.0

            # Jaccard benzerliği hesapla
            intersection = len(content_keywords.intersection(user_keywords))
            union = len(content_keywords.union(user_keywords))
            
            if union == 0:
                return 0.0

            return intersection / union

        except Exception as e:
            logger.error(f"Keyword eşleşme skoru hesaplanırken hata: {str(e)}")
            return 0.0

    def _get_user_recent_keywords(self) -> set:
        """Kullanıcının son etkileşimlerindeki keywordleri döndürür."""
        try:
            recent_keywords = set()
            # Son 100 etkileşimi kontrol et
            recent_interactions = list(self.content_engagement.items())[:100]
            
            for content_id, interactions in recent_interactions:
                # Etkileşim sayısına göre ağırlıklandır
                interaction_count = sum(interactions.values())
                if interaction_count > 0:
                    # İçeriğin keywordlerini al ve ağırlıklandır
                    content = self._get_content_by_id(content_id)
                    if content:
                        content_keywords = set(content.get('keywords', []))
                        recent_keywords.update(content_keywords)

            return recent_keywords

        except Exception as e:
            logger.error(f"Kullanıcı keywordleri alınırken hata: {str(e)}")
            return set()

    def _get_content_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """İçerik ID'sine göre içeriği döndürür."""
        # Bu fonksiyon Firebase'den içerik bilgisini alacak şekilde güncellenebilir
        # Şimdilik boş bir sözlük döndürüyoruz
        return {} 