import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from config.config import (
    COLLECTION_ADS,
    COLLECTION_AD_METRICS,
    AD_OPTIMIZATION,
    AD_FREQUENCY,
    AD_CONTENT_RATIO,
    AD_RATIO,
    EMOTION_CATEGORIES,
    KEYWORD_MATCH_WEIGHT,
    AD_PERFORMANCE_WEIGHTS
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
        self.keyword_match_weight = KEYWORD_MATCH_WEIGHT
        self.performance_weights = AD_PERFORMANCE_WEIGHTS

    def _get_ad_performance_metrics(self, ad_id: str) -> Dict[str, float]:
        """Reklamın performans metriklerini getirir."""
        try:
            metrics = self.firebase.db.collection(COLLECTION_AD_METRICS)\
                .where('ad_id', '==', ad_id)\
                .where('timestamp', '>=', (datetime.now() - timedelta(days=30)).isoformat())\
                .stream()

            total_impressions = 0
            total_clicks = 0
            total_emotion_changes = 0
            emotion_change_scores = {}

            for metric in metrics:
                metric_data = metric.to_dict()
                metric_type = metric_data.get('metric_type')

                if metric_type == 'impression':
                    total_impressions += 1
                elif metric_type == 'click':
                    total_clicks += 1
                elif metric_type.startswith('emotion_change_'):
                    total_emotion_changes += 1
                    # Duygu değişim skorunu hesapla
                    emotion_before = metric_data.get('emotion_before')
                    emotion_after = metric_data.get('emotion_after')
                    if emotion_before and emotion_after:
                        change_key = f"{emotion_before}_to_{emotion_after}"
                        emotion_change_scores[change_key] = emotion_change_scores.get(change_key, 0) + 1

            # CTR hesapla
            ctr = total_clicks / total_impressions if total_impressions > 0 else 0

            # Duygu değişim oranını hesapla
            emotion_change_ratio = total_emotion_changes / total_impressions if total_impressions > 0 else 0

            return {
                'ctr': ctr,
                'emotion_change_ratio': emotion_change_ratio,
                'emotion_change_scores': emotion_change_scores,
                'total_impressions': total_impressions,
                'total_clicks': total_clicks
            }

        except Exception as e:
            logger.error(f"Reklam performans metrikleri alınırken hata: {str(e)}")
            return {
                'ctr': 0.0,
                'emotion_change_ratio': 0.0,
                'emotion_change_scores': {},
                'total_impressions': 0,
                'total_clicks': 0
            }

    def _calculate_ad_relevance(self, ad: Dict[str, Any], content_keywords: set) -> float:
        """Reklamın içerik keywordlerine uygunluğunu hesaplar."""
        try:
            ad_keywords = set(ad.get('keywords', []))
            if not ad_keywords or not content_keywords:
                return 0.0

            # Jaccard benzerliği hesapla
            intersection = len(ad_keywords.intersection(content_keywords))
            union = len(ad_keywords.union(content_keywords))
            
            if union == 0:
                return 0.0

            return intersection / union

        except Exception as e:
            logger.error(f"Reklam uygunluğu hesaplanırken hata: {str(e)}")
            return 0.0

    def _get_best_ad_for_content(self, content: Dict[str, Any], active_ads: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """İçerik için en uygun reklamı seçer."""
        try:
            content_keywords = set(content.get('keywords', []))
            content_emotion = content.get('emotion')
            
            if not content_keywords:
                return random.choice(active_ads)

            scored_ads = []
            for ad in active_ads:
                # 1. Duygu uygunluğu
                emotion_score = 1.0 if ad.get('target_emotion') == content_emotion else 0.5
                
                # 2. Keyword uygunluğu
                keyword_score = self._calculate_ad_relevance(ad, content_keywords)
                
                # 3. Performans metrikleri
                performance_metrics = self._get_ad_performance_metrics(ad['id'])
                performance_score = self._calculate_performance_score(performance_metrics, content_emotion)
                
                # 4. Toplam skor hesaplama
                total_score = (
                    emotion_score * self.performance_weights['emotion'] +
                    keyword_score * self.performance_weights['keyword'] +
                    performance_score * self.performance_weights['performance']
                )
                
                scored_ads.append((total_score, ad))

            # En yüksek skorlu reklamı seç
            scored_ads.sort(key=lambda x: x[0], reverse=True)
            
            # Eğer yüksek performanslı reklamlar varsa, onları önceliklendir
            high_performing_ads = [
                (score, ad) for score, ad in scored_ads 
                if score > 0.7 and self._get_ad_performance_metrics(ad['id'])['ctr'] > 0.02
            ]
            
            if high_performing_ads:
                # Yüksek performanslı reklamlardan rastgele seç
                return random.choice(high_performing_ads)[1]
            
            return scored_ads[0][1] if scored_ads else None

        except Exception as e:
            logger.error(f"En uygun reklam seçilirken hata: {str(e)}")
            return random.choice(active_ads)

    def _calculate_performance_score(self, metrics: Dict[str, Any], target_emotion: str) -> float:
        """Reklam performans skorunu hesaplar."""
        try:
            # CTR skoru
            ctr_score = min(metrics['ctr'] * 10, 1.0)  # CTR'yi 0-1 arasına normalize et
            
            # Duygu değişim skoru
            emotion_change_score = 0.0
            if metrics['emotion_change_scores']:
                # Hedef duyguya yönelik değişimleri kontrol et
                for change, count in metrics['emotion_change_scores'].items():
                    if change.endswith(f"_to_{target_emotion}"):
                        emotion_change_score += count
                
                emotion_change_score = min(emotion_change_score / metrics['total_impressions'], 1.0)
            
            # Toplam performans skoru
            performance_score = (
                ctr_score * self.performance_weights['ctr'] +
                emotion_change_score * self.performance_weights['emotion_change']
            )
            
            return performance_score

        except Exception as e:
            logger.error(f"Performans skoru hesaplanırken hata: {str(e)}")
            return 0.0

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
        """Reklamları stratejik olarak yerleştirir."""
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

            # Peak moment'ten önceki içeriği al
            pre_peak_content = contents[peak_moment_index - 1]
            
            # En uygun reklamı seç
            selected_ad = self._get_best_ad_for_content(pre_peak_content, active_ads)
            
            if not selected_ad:
                selected_ad = random.choice(active_ads)

            ad_content_to_insert = {
                'id': selected_ad['id'],
                'type': 'ad',
                'is_ad': True,
                'emotion': selected_ad.get('target_emotion', 'Neşe (Joy)'),
                'content': selected_ad.get('content', 'Reklam İçeriği'),
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'advertiser_id': selected_ad.get('advertiser_id'),
                    'campaign_id': selected_ad.get('campaign_id'),
                    'keywords': selected_ad.get('keywords', []),
                    'relevance_score': self._calculate_ad_relevance(
                        selected_ad, 
                        set(pre_peak_content.get('keywords', []))
                    )
                }
            }

            result = contents[:peak_moment_index] + [ad_content_to_insert] + contents[peak_moment_index:]
            logger.info(f"[AdManager] Inserted ad {ad_content_to_insert['id']} at index {peak_moment_index}")

            self._update_ad_metrics(
                ad_content_to_insert['id'], 
                'impression', 
                user_id,
                emotion_before=pre_peak_content.get('emotion'),
                emotion_after=contents[peak_moment_index].get('emotion') if peak_moment_index < len(contents) else None
            )

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