from typing import Dict, List, Any
import random
import logging
from config import EMOTION_CATEGORIES, OPPOSITE_EMOTIONS
from services.reccomend_service.date_utils import parse_timestamp
from services.reccomend_service.shuffle_utils import shuffle_same_score
from services.reccomend_service.cold_start_utils import get_cold_start_content

class FeedGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def _handle_cold_start(self, firebase_service) -> List[Dict[str, Any]]:
        """Cold start durumunda rastgele farklı duygulardan içerik önerir"""
        try:
            # Tüm postları al
            all_posts = await firebase_service.get_all_posts()
            
            if not all_posts:
                return []

            # Farklı duygulardan 20 içerik seç
            selected_items = []
            emotions_used = set()
            
            # Her duygudan en az 2 içerik seç
            for emotion in EMOTION_CATEGORIES:
                emotion_posts = [p for p in all_posts if p.get('emotion') == emotion]
                if emotion_posts:
                    # Her duygudan 2 içerik seç
                    for _ in range(2):
                        if emotion_posts:
                            post = random.choice(emotion_posts)
                            selected_items.append({
                                'id': post['id'],
                                'type': 'post',
                                'emotion': emotion
                            })
                            emotions_used.add(emotion)
                            all_posts.remove(post)
                            emotion_posts.remove(post)

            # Kalan içerikleri rastgele doldur
            while len(selected_items) < 20 and all_posts:
                post = random.choice(all_posts)
                emotion = post.get('emotion')
                
                if emotion not in emotions_used or len(emotions_used) >= len(EMOTION_CATEGORIES):
                    selected_items.append({
                        'id': post['id'],
                        'type': 'post',
                        'emotion': emotion
                    })
                    emotions_used.add(emotion)
                all_posts.remove(post)

            # Karıştır
            random.shuffle(selected_items)
            return selected_items

        except Exception as e:
            self.logger.error(f"Cold start hatası: {str(e)}")
            return []

    async def _create_personalized_feed(
        self, 
        pattern: Dict, 
        is_continuous: bool,
        firebase_service,
        content_scorer
    ) -> List[Dict[str, Any]]:
        """Kişiselleştirilmiş içerik akışı oluşturur"""
        try:
            feed = []
            
            # Dominant duyguyu bul
            dominant_emotion = max(pattern.items(), key=lambda x: x[1])[0]
            
            # Pattern'e göre içerik oranlarını belirle
            if is_continuous:
                # Süreklilik durumunda %30 zıt duygu
                dominant_ratio = 0.6
                explore_ratio = 0.1
                opposite_ratio = 0.3
            else:
                # Normal durumda %60 dominant, %20 yeni duygu, %20 zıt
                dominant_ratio = 0.6
                explore_ratio = 0.2
                opposite_ratio = 0.2

            # Son 7 günün içeriklerini al
            recent_posts = await firebase_service.get_recent_content(days=7)
            recent_ads = await firebase_service.get_recent_ads(days=7)

            if not recent_posts:
                # Son 30 günün popüler içerikleri
                recent_posts = await firebase_service.get_popular_content(days=30)
                
            if not recent_posts:
                # Soğuk başlangıç: çeşitli ve popüler içeriklerden karışım
                all_posts = await firebase_service.get_all_posts()
                return get_cold_start_content(all_posts, list(pattern.keys()), 20)

            # İçerikleri duygu uyumuna göre sırala
            scored_posts = content_scorer.score_content(recent_posts, pattern, dominant_emotion, is_continuous)
            # Skoru aynı olanları karıştır
            scored_posts = shuffle_same_score(scored_posts)
            scored_ads = content_scorer.score_content(recent_ads, pattern, dominant_emotion, is_continuous, is_ad=True) if recent_ads else []

            # Dominant duygu içerikleri
            dominant_posts = [p for p in scored_posts if p['emotion'] == dominant_emotion]
            # Zıt duygu içerikleri
            opposite_emotions = OPPOSITE_EMOTIONS.get(dominant_emotion, [])
            opposite_posts = [p for p in scored_posts if p['emotion'] in opposite_emotions]
            # Yeni duygu keşfi için: dominant ve zıt olmayanlar
            explore_posts = [p for p in scored_posts if p['emotion'] != dominant_emotion and p['emotion'] not in opposite_emotions]

            # İçerik sayılarını hesapla
            total_posts = min(20, len(scored_posts))
            dominant_count = int(total_posts * dominant_ratio)
            explore_count = int(total_posts * explore_ratio)
            opposite_count = int(total_posts * opposite_ratio)

            # Feed'i oluştur
            post_index_dom = 0
            post_index_exp = 0
            post_index_opp = 0
            ad_index = 0
            
            # Sırayla dominant, explore ve zıt duyguları ekle
            for i in range(dominant_count):
                if post_index_dom < len(dominant_posts):
                    post = dominant_posts[post_index_dom]
                    feed.append({
                        'id': post['id'],
                        'type': 'post',
                        'emotion': post['emotion']
                    })
                    post_index_dom += 1
                    # Her 5-7 içerikte bir reklam
                    if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                        ad = scored_ads[ad_index]
                        feed.append({
                            'id': ad['id'],
                            'type': 'ad',
                            'emotion': ad.get('emotion', 'nötr')
                        })
                        ad_index += 1

            for i in range(explore_count):
                if post_index_exp < len(explore_posts):
                    post = explore_posts[post_index_exp]
                    feed.append({
                        'id': post['id'],
                        'type': 'post',
                        'emotion': post['emotion']
                    })
                    post_index_exp += 1
                    if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                        ad = scored_ads[ad_index]
                        feed.append({
                            'id': ad['id'],
                            'type': 'ad',
                            'emotion': ad.get('emotion', 'nötr')
                        })
                        ad_index += 1

            for i in range(opposite_count):
                if post_index_opp < len(opposite_posts):
                    post = opposite_posts[post_index_opp]
                    feed.append({
                        'id': post['id'],
                        'type': 'post',
                        'emotion': post['emotion']
                    })
                    post_index_opp += 1
                    if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                        ad = scored_ads[ad_index]
                        feed.append({
                            'id': ad['id'],
                            'type': 'ad',
                            'emotion': ad.get('emotion', 'nötr')
                        })
                        ad_index += 1

            return feed

        except Exception as e:
            self.logger.error(f"Kişiselleştirilmiş feed oluşturma hatası: {str(e)}")
            return [] 