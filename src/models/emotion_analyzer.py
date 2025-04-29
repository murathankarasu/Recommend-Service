import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
from config.config import (
    EMOTION_CATEGORIES,
    OPPOSITE_EMOTIONS,
    INTERACTION_TYPE_WEIGHTS,
    EMOTION_TRANSITION_MATRIX,
    EMOTION_ANALYSIS_CONFIDENCE
)

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
                                # ISO 8601 formatı (örn: 2025-04-28T22:17:49.582279)
                                dt = datetime.fromisoformat(timestamp)
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                            except Exception:
                                # Eski formatı dene
                                dt = datetime.strptime(timestamp, "%B %d, %Y at %I:%M:%S %p UTC+3")
                                dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = timestamp  # Zaten datetime ise
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
                
                if emotion not in emotion_weights:
                    emotion_weights[emotion] = 0.0
                emotion_weights[emotion] += weight
                total_weight += weight
            
            if total_weight > 0:
                for emotion in EMOTION_CATEGORIES.values():
                    weight = emotion_weights.get(emotion, 0.0)
                    current_pattern[emotion] = weight / total_weight
                
                print(f"[EmotionAnalyzer] Hesaplanan duygu deseni: {current_pattern}")
                return current_pattern
            
        except Exception as e:
            print(f"[EmotionAnalyzer ERROR] Duygu deseni analizi hatası: {str(e)}")
            return {emotion: 1.0/len(EMOTION_CATEGORIES) for emotion in EMOTION_CATEGORIES.values()}

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