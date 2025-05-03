import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config.config import (
    COLLECTION_ADS,
    COLLECTION_AD_METRICS,
    AD_OPTIMIZATION,
    AD_FREQUENCY,
    AD_CONTENT_RATIO,
    AD_RATIO,
    EMOTION_CATEGORIES
)
from services.firebase_services.firebase_base import FirebaseBase

logger = logging.getLogger(__name__)

class AdManager:
    def __init__(self, firebase_service: FirebaseBase):
        self.firebase = firebase_service
        self.ad_cache = {}  # Reklam önbelleği
        self.ad_cache_time = datetime.now()  # Önbellek güncelleme zamanı
        self.emotion_categories = EMOTION_CATEGORIES
        self.ad_frequency = AD_FREQUENCY

    def _get_ads_from_firebase(self) -> List[Dict[str, Any]]:
        """Firebase'den aktif reklamları getirir."""
        try:
            if (datetime.now() - self.ad_cache_time).total_seconds() < 300 and self.ad_cache:
                return list(self.ad_cache.values())

            ads = self.firebase.get_collection(COLLECTION_ADS)
            active_ads = [
                ad for ad in ads 
                if ad.get('is_active', False) and 
                datetime.fromisoformat(ad.get('end_date', '2000-01-01')) > datetime.now()
            ]

            self.ad_cache = {ad['id']: ad for ad in active_ads}
            self.ad_cache_time = datetime.now()

            return active_ads

        except Exception as e:
            logger.error(f"Reklamlar getirilirken hata: {str(e)}")
            return []

    def _create_ad_content(self) -> Dict[str, Any]:
        """Firebase'den reklam içeriği oluşturur."""
        try:
            ads = self._get_ads_from_firebase()
            if not ads:
                return None

            total_weight = sum(ad.get('priority', 1.0) for ad in ads)
            if total_weight == 0:
                return None

            selected_ad = None
            random_value = random.uniform(0, total_weight)
            current_sum = 0

            for ad in ads:
                current_sum += ad.get('priority', 1.0)
                if random_value <= current_sum:
                    selected_ad = ad
                    break

            if not selected_ad:
                return None

            self._update_ad_metrics(selected_ad['id'], 'impression')

            return {
                'id': selected_ad['id'],
                'type': 'ad',
                'is_ad': True,
                'emotion': selected_ad.get('target_emotion', random.choice(self.emotion_categories)),
                'content': selected_ad['content'],
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'target_emotions': selected_ad.get('target_emotions', []),
                    'priority': selected_ad.get('priority', 1.0),
                    'advertiser_id': selected_ad.get('advertiser_id'),
                    'campaign_id': selected_ad.get('campaign_id')
                }
            }

        except Exception as e:
            logger.error(f"Reklam içeriği oluşturulurken hata: {str(e)}")
            return None

    def _update_ad_metrics(self, ad_id: str, metric_type: str, user_id: str = None, 
                               emotion_before: str = None, emotion_after: str = None):
        """Reklam metriklerini günceller."""
        try:
            metric_data = {
                'ad_id': ad_id,
                'timestamp': datetime.now().isoformat(),
                'metric_type': metric_type,
                'user_id': user_id,
                'emotion_before': emotion_before,
                'emotion_after': emotion_after
            }

            self.firebase.add_document(COLLECTION_AD_METRICS, metric_data)

            ad_ref = self.firebase.db.collection(COLLECTION_ADS).document(ad_id)
            ad_ref.update({
                f'metrics.{metric_type}': self.firebase.db.FieldValue.increment(1),
                'last_updated': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Reklam metrikleri güncellenirken hata: {str(e)}")

    def track_ad_interaction(self, ad_id: str, user_id: str, interaction_type: str, 
                                 emotion_before: str = None, emotion_after: str = None):
        """Reklam etkileşimlerini takip eder."""
        try:
            metric_type = f"{interaction_type}_count"
            self._update_ad_metrics(
                ad_id, 
                metric_type, 
                user_id, 
                emotion_before, 
                emotion_after
            )

            if emotion_before and emotion_after and emotion_before != emotion_after:
                emotion_change = f"emotion_change_{emotion_before}_to_{emotion_after}"
                self._update_ad_metrics(
                    ad_id,
                    emotion_change,
                    user_id,
                    emotion_before,
                    emotion_after
                )

        except Exception as e:
            logger.error(f"Reklam etkileşimi takip edilirken hata: {str(e)}")

    def insert_ads(
        self,
        contents: List[Dict[str, Any]],
        peak_moment_index: Optional[int],
        user_id: str = None
    ) -> List[Dict[str, Any]]:
        """Inserts an ad strategically after the emotional peak moment."""
        try:
            if not contents or peak_moment_index is None or peak_moment_index <= 0 or peak_moment_index >= len(contents):
                logger.info("[AdManager] No valid peak index or contents, returning original list.")
                return contents

            ads = self.firebase.get_collection(COLLECTION_ADS)
            if not ads:
                logger.warning("[AdManager] No ads found in Firebase collection.")
                return contents

            active_ads = [
                ad for ad in ads
                if ad.get('is_active', False) and
                   parse_timestamp(ad.get('end_date', '2000-01-01')) > datetime.now(timezone.utc)
            ]

            if not active_ads:
                logger.warning("[AdManager] No active ads available.")
                return contents

            selected_ad_data = random.choice(active_ads)
            ad_content_to_insert = {
                'id': selected_ad_data['id'],
                'type': 'ad',
                'is_ad': True,
                'emotion': selected_ad_data.get('target_emotion', 'Neşe (Joy)'),
                'content': selected_ad_data.get('content', 'Reklam İçeriği'),
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'advertiser_id': selected_ad_data.get('advertiser_id'),
                    'campaign_id': selected_ad_data.get('campaign_id')
                }
            }

            result = contents[:peak_moment_index] + [ad_content_to_insert] + contents[peak_moment_index:]
            logger.info(f"[AdManager] Inserted ad {ad_content_to_insert['id']} at index {peak_moment_index}")

            self._update_ad_metrics(ad_content_to_insert['id'], 'impression', user_id)

            return result

        except Exception as e:
            logger.error(f"[AdManager ERROR] Error inserting ad: {str(e)}", exc_info=True)
            return contents

    def _optimize_ad_placement(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reklam yerleşimini optimize eder"""
        ad_count = 0
        optimized_recommendations = []
        
        for rec in recommendations:
            if rec.get('is_ad', False):
                if ad_count >= AD_OPTIMIZATION['frequency_cap']:
                    continue
                ad_count += 1
            
            optimized_recommendations.append(rec)
        
        return optimized_recommendations 

def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        logger.debug(f"Could not parse timestamp: {timestamp_str}")
        return None
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None 