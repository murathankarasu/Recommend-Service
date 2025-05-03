import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from config.config import (
    EMOTION_CATEGORIES,
    OPPOSITE_EMOTIONS,
    INTERACTION_TYPE_WEIGHTS,
    EMOTION_TRANSITION_MATRIX,
    EMOTION_ANALYSIS_CONFIDENCE
)
from services.reccomend_service.date_utils import parse_timestamp

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    def __init__(self):
        self.emotion_categories = EMOTION_CATEGORIES
        self.opposite_emotions = OPPOSITE_EMOTIONS
        self.interaction_weights = INTERACTION_TYPE_WEIGHTS

    def analyze_pattern(self, interactions: List[Dict], user_id: str) -> Dict[str, float]:
        """Kullanıcının duygu desenini analiz eder"""
        try:
            print(f"[EmotionAnalyzer] Duygu deseni analizi başlatılıyor - Kullanıcı: {user_id}")
            current_pattern = {emotion: 0.0 for emotion in EMOTION_CATEGORIES.values()}
            if not interactions:
                return current_pattern
            emotion_weights = {}
            total_weight = 0.0
            dislike_emotions = set()
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            for interaction in interactions:
                emotion = interaction.get('emotion')
                if not emotion or emotion not in EMOTION_CATEGORIES.values():
                    continue
                weight = 1.0
                interaction_type = interaction.get('interactionType')
                if interaction_type:
                    weight *= self.interaction_weights.get(interaction_type, 1.0)
                confidence = interaction.get('confidence', 0.5)
                weight *= confidence
                timestamp = interaction.get('timestamp')
                if timestamp:
                    try:
                        dt = None
                        if isinstance(timestamp, str):
                            try:
                                dt = datetime.fromisoformat(timestamp)
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                            except Exception:
                                dt = datetime.strptime(timestamp, "%B %d, %Y at %I:%M:%S %p UTC+3")
                                dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = timestamp
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                        if dt >= last_24h:
                            weight *= 2.0
                        elif dt >= last_7d:
                            weight *= 1.5
                        else:
                            days_old = (now - dt).days
                            weight *= max(0.5, 1.0 - (days_old * 0.1))
                    except Exception as e:
                        print(f"[EmotionAnalyzer WARNING] Timestamp dönüştürme hatası: {str(e)}")
                if interaction_type == "dislike":
                    dislike_emotions.add(emotion)
                if emotion not in emotion_weights:
                    emotion_weights[emotion] = 0.0
                emotion_weights[emotion] += weight
                total_weight += weight
            # 1. Pattern'i normalize et
            positive_sum = sum(max(0.0, w) for w in emotion_weights.values())
            for emotion in EMOTION_CATEGORIES.values():
                weight = max(0.0, emotion_weights.get(emotion, 0.0))
                current_pattern[emotion] = weight / positive_sum if positive_sum > 0 else 0.0
            # 2. Dislike varsa pattern oranını azalt
            for disliked_emotion in dislike_emotions:
                if disliked_emotion in current_pattern:
                    if current_pattern[disliked_emotion] > 0.5:
                        current_pattern[disliked_emotion] = 0.5
                    else:
                        current_pattern[disliked_emotion] *= 0.975
            # 3. Tekrar normalize et
            norm_sum = sum(current_pattern.values())
            if norm_sum > 0:
                for emotion in current_pattern:
                    current_pattern[emotion] /= norm_sum
            print(f"[EmotionAnalyzer] Hesaplanan duygu deseni: {current_pattern}")
            return current_pattern
        except Exception as e:
            print(f"[EmotionAnalyzer ERROR] Duygu deseni analizi hatası: {str(e)}")
            return {emotion: 1.0/len(EMOTION_CATEGORIES) for emotion in EMOTION_CATEGORIES.values()}

    def analyze_transition_patterns(self, interactions: List[Dict]) -> Dict[Tuple[str, str], int]:
        """
        Analyzes the user's historical interactions to count emotion transitions.

        Args:
            interactions: List of user interaction dictionaries, ideally sorted by timestamp.

        Returns:
            A dictionary where keys are (from_emotion, to_emotion) tuples
            and values are the count of that transition observed.
            Example: {('Sadness', 'Joy'): 5, ('Joy', 'Surprise'): 3}
        """
        transition_counts = defaultdict(int)
        if len(interactions) < 2:
            return {}

        # Ensure interactions are sorted by time for accurate transitions
        sorted_interactions = []
        try:
            interactions_with_dt = []
            for i in interactions:
                dt = parse_timestamp(i.get('timestamp'))
                emotion = i.get('emotion')
                # Include only interactions with valid timestamps and emotions for transition analysis
                if dt and emotion and emotion in self.emotion_categories.values():
                    interactions_with_dt.append((dt, i))

            if len(interactions_with_dt) < 2:
                return {}

            interactions_with_dt.sort(key=lambda x: x[0]) # Sort ascending by time
            sorted_interactions = [item[1] for item in interactions_with_dt]

        except Exception as e:
            logger.warning(f"Could not sort interactions for transition analysis: {e}. Returning empty transitions.")
            return {}

        # Count transitions between consecutive interactions
        for i in range(len(sorted_interactions) - 1):
            from_emotion = sorted_interactions[i].get('emotion')
            to_emotion = sorted_interactions[i+1].get('emotion')

            # We already pre-filtered for valid emotions during sorting prep
            if from_emotion and to_emotion:
                transition_counts[(from_emotion, to_emotion)] += 1

        logger.info(f"Analyzed user transitions: Found {len(transition_counts)} unique transitions.")
        # Optional: Convert counts to probabilities if needed later, but counts are fine for now.
        # total_transitions_from = defaultdict(int)
        # for (from_e, to_e), count in transition_counts.items():
        #     total_transitions_from[from_e] += count
        # transition_probabilities = {trans: count / total_transitions_from[trans[0]]
        #                           for trans, count in transition_counts.items()
        #                           if total_transitions_from[trans[0]] > 0}

        return dict(transition_counts) # Convert back to regular dict

    def get_current_emotion_and_transitions(self, interactions: List[Dict]) -> Tuple[Optional[str], Dict[str, float]]:
        """
        Finds the most recent interaction's emotion as the 'current emotion'
        and predicts potential next emotions using the transition matrix.

        Returns:
            Tuple[Optional[str], Dict[str, float]]:
                - The determined current emotion (or None if no valid recent interaction).
                - A dictionary of {next_emotion: probability} based on the transition matrix.
        """
        if not interactions:
            return None, {}

        # Sort interactions by timestamp descending to find the latest one
        try:
            # Attempt to parse timestamps and sort
            interactions_with_dt = []
            for i in interactions:
                dt = parse_timestamp(i.get('timestamp'))
                if dt:
                    interactions_with_dt.append((dt, i))

            if not interactions_with_dt:
                 # Fallback if no parsable timestamps: assume list is somewhat ordered
                 # or just take the last element might be risky
                 # Let's try taking the last one with a valid emotion
                last_interaction = None
                for i in reversed(interactions):
                    if i.get('emotion') in self.emotion_categories.values():
                        last_interaction = i
                        break
            else:
                interactions_with_dt.sort(key=lambda x: x[0], reverse=True)
                last_interaction = interactions_with_dt[0][1]

        except Exception as e:
            logger.warning(f"Could not sort interactions by timestamp: {e}")
            # Fallback: try finding the last interaction with a valid emotion
            last_interaction = None
            for i in reversed(interactions):
                 if i.get('emotion') in self.emotion_categories.values():
                    last_interaction = i
                    break

        if not last_interaction:
            return None, {}

        current_emotion = last_interaction.get('emotion')

        if current_emotion not in self.emotion_categories.values():
             return None, {} # Invalid emotion

        # Predict next emotions using the transition matrix
        predicted_transitions = self._predict_emotion_transition(current_emotion)

        logger.info(f"Current emotion determined as: {current_emotion}")
        logger.info(f"Predicted next transitions: {predicted_transitions}")

        return current_emotion, predicted_transitions

    def _check_emotion_continuity(self, interactions: List[Dict[str, Any]]) -> bool:
        """Kullanıcının tek duyguda takılıp kalmadığını kontrol eder"""
        if not interactions:
            return False

        recent_interactions = sorted(
            interactions, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:10]

        if len(recent_interactions) < 10:
            return False

        emotions = [i.get('emotion') for i in recent_interactions]
        dominant_emotion = max(set(emotions), key=emotions.count)

        return emotions.count(dominant_emotion) >= 8

    def _predict_emotion_transition(self, current_emotion: str) -> Dict[str, float]:
        """Duygu geçiş olasılıklarını tahmin eder"""
        return EMOTION_TRANSITION_MATRIX.get(current_emotion, {})

    def _get_emotion_confidence(self, emotion_score: float) -> str:
        """Duygu analizi güven skorunu hesaplar"""
        if emotion_score >= EMOTION_ANALYSIS_CONFIDENCE['high_confidence_threshold']:
            return 'high'
        elif emotion_score >= EMOTION_ANALYSIS_CONFIDENCE['medium_confidence_threshold']:
            return 'medium'
        elif emotion_score >= EMOTION_ANALYSIS_CONFIDENCE['low_confidence_threshold']:
            return 'low'
        return 'very_low' 