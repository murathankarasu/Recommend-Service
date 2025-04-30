import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class WordAnalyzer:
    def __init__(self):
        self.word_analysis = {}  # Kelime analizi verileri
        self.word_emotion_mapping = {}  # Kelime-duygu eşleştirmesi

    def _analyze_content_words(self, content: str, emotion: str) -> None:
        """İçerikteki kelimeleri analiz eder ve duygu ile eşleştirir"""
        try:
            words = content.lower().split()
            
            for word in words:
                word = word.strip('.,!?()[]{}"\'')
                if len(word) < 3:
                    continue
                
                if word not in self.word_analysis:
                    self.word_analysis[word] = {
                        'count': 0,
                        'emotions': {},
                        'total_interactions': 0
                    }
                
                self.word_analysis[word]['count'] += 1
                self.word_analysis[word]['emotions'][emotion] = self.word_analysis[word]['emotions'].get(emotion, 0) + 1
                self.word_analysis[word]['total_interactions'] += 1
                
                if word not in self.word_emotion_mapping:
                    self.word_emotion_mapping[word] = {}
                self.word_emotion_mapping[word][emotion] = self.word_emotion_mapping[word].get(emotion, 0) + 1
                
        except Exception as e:
            logger.error(f"Kelime analizi hatası: {str(e)}")

    def _calculate_word_emotion_score(self, word: str, target_emotion: str) -> float:
        """Kelimenin belirli bir duyguya olan bağlantısını hesaplar"""
        try:
            if word not in self.word_emotion_mapping:
                return 0.0
            
            word_data = self.word_emotion_mapping[word]
            total_occurrences = sum(word_data.values())
            
            if total_occurrences == 0:
                return 0.0
            
            emotion_score = word_data.get(target_emotion, 0) / total_occurrences
            interaction_weight = min(self.word_analysis[word]['total_interactions'] / 100, 1.0)
            
            return emotion_score * interaction_weight
            
        except Exception as e:
            logger.error(f"Kelime duygu skoru hesaplama hatası: {str(e)}")
            return 0.0

    def _calculate_content_word_match(self, content: str, user_words: Dict[str, float]) -> float:
        """İçeriğin kullanıcının etkileşimde bulunduğu kelimelerle eşleşme oranını hesaplar"""
        try:
            content_words = set(content.lower().split())
            total_score = 0.0
            
            for word in content_words:
                word = word.strip('.,!?()[]{}"\'')
                if word in user_words:
                    word_importance = user_words[word]
                    total_score += word_importance
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"İçerik kelime eşleşme skoru hesaplama hatası: {str(e)}")
            return 0.0

    def analyze_content(self, content: str, emotion: str) -> Dict[str, float]:
        """İçeriği analiz eder ve kelime-duygu eşleştirmelerini döndürür"""
        try:
            self._analyze_content_words(content, emotion)
            
            word_scores = {}
            for word in content.lower().split():
                word = word.strip('.,!?()[]{}"\'')
                if word in self.word_analysis:
                    word_scores[word] = self._calculate_word_emotion_score(word, emotion)
            
            return word_scores
            
        except Exception as e:
            logger.error(f"İçerik analizi hatası: {str(e)}")
            return {} 