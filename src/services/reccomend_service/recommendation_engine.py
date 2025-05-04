from typing import Dict, List, Any
import logging
from models.emotion_model import EmotionModel
from services.content_scorer import ContentScorer
from services.feed_generator import FeedGenerator
from services.pattern_manager import PatternManager
# --- Yardımcı modüller ---
from services.reccomend_service.user_history_utils import get_recent_shown_post_ids
from services.reccomend_service.ab_test_logger import log_recommendation_event
from services.reccomend_service.cold_start_utils import get_cold_start_content
from config.config import EMOTION_CATEGORIES

class RecommendationEngine:
    def __init__(
        self,
        emotion_model: EmotionModel,
        content_scorer: ContentScorer,
        feed_generator: FeedGenerator,
        pattern_manager: PatternManager
    ):
        self.logger = logging.getLogger(__name__)
        self.emotion_model = emotion_model
        self.content_scorer = content_scorer
        self.feed_generator = feed_generator
        self.pattern_manager = pattern_manager

    async def generate_recommendations(
        self,
        user_id: str,
        limit: int = 20,
        firebase_service = None
    ) -> Dict[str, Any]:
        """Kullanıcı için önerileri oluşturur"""
        try:
            print(f"[RecommendationEngine] Öneriler oluşturuluyor - Kullanıcı: {user_id}")
            # Kullanıcı etkileşimlerini getir
            interactions = firebase_service.get_user_interactions(user_id)
            # İçerikleri getir
            contents = firebase_service.get_all_posts()
            # Soğuk başlangıç kontrolü
            if not interactions:
                content_mix = get_cold_start_content(contents, list(EMOTION_CATEGORIES.values()), limit)
                emotion_pattern = {e: 1/len(EMOTION_CATEGORIES) for e in EMOTION_CATEGORIES.values()}
            else:
                # Duygu desenini analiz et
                emotion_pattern = self.emotion_model.analyze_pattern(interactions, user_id)
                # Kullanıcıya daha önce gösterilen postId'leri topla (son 200)
                shown_post_ids = get_recent_shown_post_ids(interactions)
                # İçerik karışımını oluştur (daha önce gösterilenleri hariç tut)
                content_mix = self.emotion_model.get_content_mix(contents, emotion_pattern, limit, shown_post_ids=shown_post_ids)
            # Reklamları ekle
            final_mix = self.emotion_model.insert_ads(content_mix, user_id)
            # Loglama (A/B test ve parametre takibi)
            try:
                log_recommendation_event(
                    user_id=user_id,
                    recommended_posts=[c['id'] for c in final_mix if 'id' in c],
                    params={"repeat_ratio": 0.2, "cold_start": not bool(interactions)}
                )
            except Exception as logerr:
                print(f"[RecommendationEngine] Loglama hatası: {logerr}")
            return {
                'success': True,
                'recommendations': final_mix,
                'emotion_pattern': emotion_pattern
            }
        except Exception as e:
            print(f"[RecommendationEngine ERROR] Öneri oluşturma hatası: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': [],
                'emotion_pattern': {}
            }

    async def generate_user_feed(
        self,
        user_id: str,
        firebase_service
    ) -> List[Dict[str, Any]]:
        """Kullanıcı için feed oluşturur"""
        try:
            # Kullanıcı verilerini al
            user_data = firebase_service.get_user_emotion_data(user_id)
            interactions = user_data.get('interactions', [])
            # Süreklilik kontrolü
            is_continuous = self.pattern_manager._check_emotion_continuity(interactions)
            # Pattern'i al
            pattern = firebase_service.get_user_pattern(user_id)
            # Feed oluştur
            feed = self.feed_generator._create_personalized_feed(
                pattern, 
                is_continuous,
                firebase_service,
                self.content_scorer
            )
            return feed
        except Exception as e:
            self.logger.error(f"Feed oluşturma hatası: {str(e)}")
            return self.feed_generator._handle_cold_start(firebase_service) 