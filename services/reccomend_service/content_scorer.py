from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

class ContentScorer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def score_content(
        self, 
        contents: List[Dict], 
        pattern: Dict, 
        dominant_emotion: str, 
        is_continuous: bool,
        is_ad: bool = False
    ) -> List[Dict]:
        """İçerikleri kullanıcı pattern'ine göre skorlar"""
        scored_contents = []
        
        for content in contents:
            score = 0
            content_emotion = content.get('emotion')
            
            # Temel uyum skoru
            emotion_match = pattern.get(content_emotion, 0)
            score += emotion_match
            
            # Süreklilik durumunda zıt duyguları öne çıkar
            if is_continuous and content_emotion in OPPOSITE_EMOTIONS.get(dominant_emotion, []):
                score *= 1.3
            
            # Yeni içeriklere bonus
            days_old = (datetime.now() - content['created_at']).days
            if days_old <= 7:
                score *= 1.2
            
            # Reklamlar için ek skorlama
            if is_ad:
                ctr = content.get('ctr', 0)
                score *= (1 + ctr)
            
            scored_contents.append({
                **content,
                '_score': score
            })
        
        # Skora göre sırala
        return sorted(scored_contents, key=lambda x: x['_score'], reverse=True)

    def calculate_relevance_score(self, post: Dict[str, Any], interactions: List[Dict[str, Any]], pattern: Dict[str, float]) -> float:
        """Post için ilgi skoru hesaplar."""
        try:
            print(f"[Recommendation] İlgi skoru hesaplanıyor - Post ID: {post.get('id')}")
            
            # Temel skor
            base_score = 1.0
            
            # Etkileşim bazlı skor
            interaction_score = 0.0
            for interaction in interactions:
                if interaction['content_id'] == post['id']:
                    interaction_score += interaction['weight']
            print(f"[Recommendation] Etkileşim skoru: {interaction_score}")
            
            # Duygu uyumu skoru
            emotion_score = 0.0
            post_emotions = post.get('emotions', {})
            for emotion, weight in pattern.items():
                if emotion in post_emotions:
                    emotion_score += weight * post_emotions[emotion]
            print(f"[Recommendation] Duygu uyumu skoru: {emotion_score}")
            
            # Zaman bazlı skor (yeni içerikler daha yüksek skor alır)
            time_score = 0.0
            if 'timestamp' in post:
                time_diff = datetime.now() - post['timestamp']
                time_score = 1.0 / (1.0 + time_diff.days)
            print(f"[Recommendation] Zaman skoru: {time_score}")
            
            # Toplam skor
            total_score = base_score + interaction_score + emotion_score + time_score
            print(f"[Recommendation] Toplam skor: {total_score}")
            
            return total_score
            
        except Exception as e:
            print(f"[Recommendation ERROR] İlgi skoru hesaplanırken hata: {str(e)}")
            return 0.0 