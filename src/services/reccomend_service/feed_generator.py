from typing import Dict, List, Any
import random
import logging
from config import EMOTION_CATEGORIES, OPPOSITE_EMOTIONS
from services.reccomend_service.date_utils import parse_timestamp
from services.reccomend_service.shuffle_utils import shuffle_same_score
from services.reccomend_service.cold_start_utils import get_cold_start_content
import datetime
from services.reccomend_service.algorithms.emotion_transition import analyze_emotion_transition

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

    def get_time_of_day():
        now = datetime.datetime.now()
        hour = now.hour
        if 6 <= hour < 12:
            return 'sabah'
        elif 12 <= hour < 18:
            return 'ogle'
        elif 18 <= hour < 24:
            return 'aksam'
        else:
            return 'gece'

    POSITIVE_EMOTIONS = ["Neşe (Joy)", "Aşk (Love)", "Şaşkınlık (Surprise)"]
    NEGATIVE_EMOTIONS = ["Üzüntü (Sadness)", "Korku (Fear)", "Öfke (Anger)"]

    # Pattern'i günün saatine göre ağırlıklandır

    def adjust_pattern_by_time(pattern: dict) -> dict:
        time_of_day = get_time_of_day()
        new_pattern = pattern.copy()
        if time_of_day == 'sabah':
            # Sabah pozitif duygulara ağırlık ver
            for e in POSITIVE_EMOTIONS:
                if e in new_pattern:
                    new_pattern[e] *= 1.2
            for e in NEGATIVE_EMOTIONS:
                if e in new_pattern:
                    new_pattern[e] *= 0.8
        elif time_of_day == 'aksam' or time_of_day == 'gece':
            # Akşam/gece negatif duygulara ağırlık ver
            for e in NEGATIVE_EMOTIONS:
                if e in new_pattern:
                    new_pattern[e] *= 1.2
            for e in POSITIVE_EMOTIONS:
                if e in new_pattern:
                    new_pattern[e] *= 0.8
        # Normalize et
        total = sum(new_pattern.values())
        if total > 0:
            for e in new_pattern:
                new_pattern[e] /= total
        return new_pattern

    # Sürpriz içerik ekle

    def inject_surprise_content(feed, all_contents, pattern, ratio=0.1):
        # Pattern'de düşük veya sıfır olan duyguları bul
        min_val = min(pattern.values())
        surprise_emotions = [e for e, v in pattern.items() if v == min_val]
        candidates = [c for c in all_contents if c.get('emotion') in surprise_emotions and c not in feed]
        n_surprise = max(1, int(len(feed) * ratio))
        if not candidates:
            return feed
        surprise_items = random.sample(candidates, min(n_surprise, len(candidates)))
        # Rastgele yerlere ekle
        for item in surprise_items:
            idx = random.randint(0, len(feed))
            feed.insert(idx, item)
        return feed

    def find_striking_transition(feed_emotions, pattern):
        """
        Feed'deki duygusal akışta en vurucu geçişin indeksini bulur.
        Kriter: pattern'de düşükten yükseğe geçiş veya pozitif-negatif zıtlık.
        """
        max_delta = 0
        striking_idx = None
        for i in range(1, len(feed_emotions)):
            prev, curr = feed_emotions[i-1], feed_emotions[i]
            if prev == curr:
                continue
            # Pattern farkı
            delta = abs(pattern.get(curr, 0) - pattern.get(prev, 0))
            # Pozitif-negatif zıtlık
            zıtlik = (prev in POSITIVE_EMOTIONS and curr in NEGATIVE_EMOTIONS) or (prev in NEGATIVE_EMOTIONS and curr in POSITIVE_EMOTIONS)
            score = delta + (0.2 if zıtlik else 0)
            if score > max_delta:
                max_delta = score
                striking_idx = i
        return striking_idx

    async def _create_personalized_feed(
        self, 
        pattern: Dict, 
        is_continuous: bool,
        firebase_service,
        content_scorer,
        user_id: str = None
    ) -> List[Dict[str, Any]]:
        """Kişiselleştirilmiş içerik akışı oluşturur"""
        try:
            feed = []
            pattern = self.adjust_pattern_by_time(pattern)
            total_posts = 20
            if is_continuous:
                # Tekrar eden duygu durumunda: %40 dominant, %40 zıt, %20 keşif
                dominant_ratio = 0.4
                opposite_ratio = 0.4
                explore_ratio = 0.2
            else:
                # Normal durumda: %60 dominant, %20 zıt, %20 keşif
                dominant_ratio = 0.6
                opposite_ratio = 0.2
                explore_ratio = 0.2
            dominant_count = int(total_posts * dominant_ratio)
            opposite_count = int(total_posts * opposite_ratio)
            explore_count = total_posts - dominant_count - opposite_count
            # Son 7 günün içeriklerini al
            recent_posts = await firebase_service.get_recent_content(days=7)
            recent_ads = await firebase_service.get_recent_ads(days=7)
            if not recent_posts:
                recent_posts = await firebase_service.get_popular_content(days=30)
            if not recent_posts:
                all_posts = await firebase_service.get_all_posts()
                return get_cold_start_content(all_posts, list(pattern.keys()), total_posts)
            scored_posts = content_scorer.score_content(recent_posts, pattern, max(pattern.items(), key=lambda x: x[1])[0], is_continuous)
            scored_posts = shuffle_same_score(scored_posts)
            scored_ads = content_scorer.score_content(recent_ads, pattern, max(pattern.items(), key=lambda x: x[1])[0], is_continuous, is_ad=True) if recent_ads else []
            dominant_posts = [p for p in scored_posts if p['emotion'] == max(pattern.items(), key=lambda x: x[1])[0]]
            opposite_emotions = OPPOSITE_EMOTIONS.get(max(pattern.items(), key=lambda x: x[1])[0], [])
            opposite_posts = [p for p in scored_posts if p['emotion'] in opposite_emotions]
            explore_emotions = [e for e in pattern.keys() if e != max(pattern.items(), key=lambda x: x[1])[0] and e not in opposite_emotions]
            explore_posts = [p for p in scored_posts if p['emotion'] in explore_emotions]
            # Zıt ve keşif duygular pattern'e göre kendi aralarında dağıtılır
            # Zıt duygular
            opp_pattern_sum = sum([pattern[e] for e in opposite_emotions])
            opp_emotion_counts = {}
            for e in opposite_emotions:
                if opp_pattern_sum > 0:
                    opp_emotion_counts[e] = int(opposite_count * (pattern[e] / opp_pattern_sum))
                else:
                    opp_emotion_counts[e] = 0
            kalan_opp = opposite_count - sum(opp_emotion_counts.values())
            for e in opposite_emotions:
                if kalan_opp <= 0:
                    break
                opp_emotion_counts[e] += 1
                kalan_opp -= 1
            # Keşif duygular
            exp_pattern_sum = sum([pattern[e] for e in explore_emotions])
            exp_emotion_counts = {}
            for e in explore_emotions:
                if exp_pattern_sum > 0:
                    exp_emotion_counts[e] = int(explore_count * (pattern[e] / exp_pattern_sum))
                else:
                    exp_emotion_counts[e] = 0
            kalan_exp = explore_count - sum(exp_emotion_counts.values())
            for e in explore_emotions:
                if kalan_exp <= 0:
                    break
                exp_emotion_counts[e] += 1
                kalan_exp -= 1
            # Feed'i oluştur
            post_index_dom = 0
            ad_index = 0
            # Dominant duygudan ekle
            for i in range(dominant_count):
                if post_index_dom < len(dominant_posts):
                    post = dominant_posts[post_index_dom]
                    feed.append({
                        'id': post['id'],
                        'type': 'post',
                        'emotion': post['emotion']
                    })
                    post_index_dom += 1
                    if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                        ad = scored_ads[ad_index]
                        feed.append({
                            'id': ad['id'],
                            'type': 'ad',
                            'emotion': ad.get('emotion', 'nötr')
                        })
                        ad_index += 1
            # Zıt duygulardan ekle
            for e in opposite_emotions:
                count = opp_emotion_counts[e]
                posts = [p for p in opposite_posts if p['emotion'] == e]
                post_index = 0
                for i in range(count):
                    if post_index < len(posts):
                        post = posts[post_index]
                        feed.append({
                            'id': post['id'],
                            'type': 'post',
                            'emotion': post['emotion']
                        })
                        post_index += 1
                        if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                            ad = scored_ads[ad_index]
                            feed.append({
                                'id': ad['id'],
                                'type': 'ad',
                                'emotion': ad.get('emotion', 'nötr')
                            })
                            ad_index += 1
            # Keşif duygulardan ekle
            for e in explore_emotions:
                count = exp_emotion_counts[e]
                posts = [p for p in explore_posts if p['emotion'] == e]
                post_index = 0
                for i in range(count):
                    if post_index < len(posts):
                        post = posts[post_index]
                        feed.append({
                            'id': post['id'],
                            'type': 'post',
                            'emotion': post['emotion']
                        })
                        post_index += 1
                        if len(feed) % random.randint(5, 7) == 0 and ad_index < len(scored_ads):
                            ad = scored_ads[ad_index]
                            feed.append({
                                'id': ad['id'],
                                'type': 'ad',
                                'emotion': ad.get('emotion', 'nötr')
                            })
                            ad_index += 1
            # Feed oluşturulduktan sonra sürpriz içerik ekle
            all_posts = await firebase_service.get_all_posts()
            feed = self.inject_surprise_content(feed, all_posts, pattern, ratio=0.1)
            feed = avoid_consecutive_same_emotion(feed)
            # --- HİKAYE AKIŞI ANALİZİ ve KAYDI ---
            if user_id is not None:
                user_data = await firebase_service.get_user_emotion_data(user_id)
                interactions = user_data.get('interactions', [])
                emotions = [i.get('emotion') for i in interactions if i.get('emotion')]
                story_flow = []
                for i in range(1, len(emotions)):
                    if emotions[i-1] != emotions[i]:
                        story_flow.append(f"{emotions[i-1]} -> {emotions[i]}")
                feed_emotions = [item.get('emotion') for item in feed if item.get('type') == 'post']
                for i in range(1, len(feed_emotions)):
                    if feed_emotions[i-1] != feed_emotions[i]:
                        story_flow.append(f"{feed_emotions[i-1]} -> {feed_emotions[i]}")
                await firebase_service.save_user_story_flow(user_id, story_flow)
            # --- VURGU GEÇİŞİNE REKLAM EKLEME ---
            feed_emotions = [item.get('emotion') for item in feed if item.get('type') == 'post']
            striking_idx = self.find_striking_transition(feed_emotions, pattern)
            if striking_idx is not None:
                # Reklamı bu geçişin hemen sonrasına ekle (varsa reklam havuzundan al)
                recent_ads = await firebase_service.get_recent_ads(days=7)
                scored_ads = content_scorer.score_content(recent_ads, pattern, max(pattern.items(), key=lambda x: x[1])[0], is_continuous, is_ad=True) if recent_ads else []
                if scored_ads:
                    ad = scored_ads[0]
                    # Post sıralamasında striking_idx'e karşılık gelen feed indexini bul
                    post_indices = [i for i, item in enumerate(feed) if item.get('type') == 'post']
                    if striking_idx < len(post_indices):
                        insert_idx = post_indices[striking_idx] + 1
                        feed.insert(insert_idx, {
                            'id': ad['id'],
                            'type': 'ad',
                            'emotion': ad.get('emotion', 'nötr')
                        })
            return feed
        except Exception as e:
            self.logger.error(f"Kişiselleştirilmiş feed oluşturma hatası: {str(e)}")
            return []

def avoid_consecutive_same_emotion(feed: list) -> list:
    """
    Feed'de arka arkaya aynı duygudan post gelmesini minimize eder.
    """
    if not feed:
        return feed
    result = []
    pool = feed.copy()
    last_emotion = None
    while pool:
        # Öncelikle farklı duygudan olanları seç
        candidates = [item for item in pool if item.get('emotion') != last_emotion or item.get('type') == 'ad']
        if not candidates:
            # Mecburen aynı duygudan devam et
            candidates = pool
        chosen = random.choice(candidates)
        result.append(chosen)
        pool.remove(chosen)
        if chosen.get('type') == 'post':
            last_emotion = chosen.get('emotion')
    return result 