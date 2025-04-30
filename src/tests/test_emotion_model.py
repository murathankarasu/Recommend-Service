import unittest
import asyncio
from datetime import datetime, timedelta
from src.models.emotion_model import EmotionModel
from src.config import (
    EMOTION_CATEGORIES,
    COLLECTION_ADS,
    COLLECTION_AD_METRICS
)

class TestEmotionModel(unittest.TestCase):
    def setUp(self):
        self.model = EmotionModel()
        self.sample_interactions = [
            {'emotion': 'mutlu', 'type': 'like', 'timestamp': datetime.now().isoformat()},
            {'emotion': 'mutlu', 'type': 'share', 'timestamp': datetime.now().isoformat()},
            {'emotion': 'üzgün', 'type': 'view', 'timestamp': datetime.now().isoformat()},
            {'emotion': 'kızgın', 'type': 'comment', 'timestamp': datetime.now().isoformat()}
        ]
        self.sample_contents = [
            {'id': '1', 'emotion': 'mutlu', 'content': 'Mutlu içerik'},
            {'id': '2', 'emotion': 'üzgün', 'content': 'Üzgün içerik'},
            {'id': '3', 'emotion': 'kızgın', 'content': 'Kızgın içerik'},
            {'id': '4', 'emotion': 'nötr', 'content': 'Nötr içerik'}
        ]
        self.sample_ad = {
            'id': 'test_ad_1',
            'content': 'Test Reklamı',
            'is_active': True,
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=1)).isoformat(),
            'target_emotion': 'mutlu',
            'target_emotions': ['mutlu', 'şaşkın'],
            'priority': 1.0,
            'advertiser_id': 'test_advertiser',
            'campaign_id': 'test_campaign',
            'metrics': {
                'impression_count': 0,
                'click_count': 0,
                'emotion_changes': {}
            }
        }

    def test_analyze_pattern(self):
        pattern = self.model.analyze_pattern(self.sample_interactions)
        self.assertIsInstance(pattern, dict)
        self.assertEqual(len(pattern), len(self.model.emotion_categories))
        self.assertAlmostEqual(sum(pattern.values()), 1.0)

    def test_calculate_content_relevance(self):
        pattern = self.model.analyze_pattern(self.sample_interactions)
        content = self.sample_contents[0]
        relevance = self.model.calculate_content_relevance(content, pattern)
        self.assertIsInstance(relevance, float)
        self.assertGreaterEqual(relevance, 0.0)
        self.assertLessEqual(relevance, 1.0)

    def test_get_content_mix(self):
        pattern = self.model.analyze_pattern(self.sample_interactions)
        content_mix = self.model.get_content_mix(self.sample_contents, pattern, 3)
        self.assertIsInstance(content_mix, list)
        self.assertLessEqual(len(content_mix), 3)

    async def test_get_ads_from_firebase(self):
        """Firebase'den reklam getirme testi"""
        # Test reklamını Firebase'e ekle
        await self.model.firebase.add_document(COLLECTION_ADS, self.sample_ad)
        
        # Reklamları getir
        ads = await self.model._get_ads_from_firebase()
        
        # Test et
        self.assertIsInstance(ads, list)
        self.assertGreater(len(ads), 0)
        self.assertEqual(ads[0]['id'], self.sample_ad['id'])

    async def test_create_ad_content(self):
        """Reklam içeriği oluşturma testi"""
        # Test reklamını Firebase'e ekle
        await self.model.firebase.add_document(COLLECTION_ADS, self.sample_ad)
        
        # Reklam içeriği oluştur
        ad_content = await self.model._create_ad_content()
        
        # Test et
        self.assertIsNotNone(ad_content)
        self.assertEqual(ad_content['type'], 'ad')
        self.assertTrue(ad_content['is_ad'])
        self.assertIn('metadata', ad_content)

    async def test_update_ad_metrics(self):
        """Reklam metriklerini güncelleme testi"""
        # Test reklamını Firebase'e ekle
        await self.model.firebase.add_document(COLLECTION_ADS, self.sample_ad)
        
        # Metrik güncelle
        await self.model._update_ad_metrics(
            self.sample_ad['id'],
            'impression',
            'test_user',
            'mutlu',
            'şaşkın'
        )
        
        # Metrikleri kontrol et
        ad_ref = self.model.firebase.db.collection(COLLECTION_ADS).document(self.sample_ad['id'])
        ad_data = await ad_ref.get()
        ad_data = ad_data.to_dict()
        
        self.assertEqual(ad_data['metrics']['impression_count'], 1)

    async def test_track_ad_interaction(self):
        """Reklam etkileşimi takip testi"""
        # Test reklamını Firebase'e ekle
        await self.model.firebase.add_document(COLLECTION_ADS, self.sample_ad)
        
        # Etkileşim takibi
        await self.model.track_ad_interaction(
            self.sample_ad['id'],
            'test_user',
            'click',
            'mutlu',
            'şaşkın'
        )
        
        # Metrikleri kontrol et
        ad_ref = self.model.firebase.db.collection(COLLECTION_ADS).document(self.sample_ad['id'])
        ad_data = await ad_ref.get()
        ad_data = ad_data.to_dict()
        
        self.assertEqual(ad_data['metrics']['click_count'], 1)
        self.assertIn('emotion_change_mutlu_to_şaşkın', ad_data['metrics']['emotion_changes'])

    async def test_insert_ads(self):
        """Reklam ekleme testi"""
        # Test reklamını Firebase'e ekle
        await self.model.firebase.add_document(COLLECTION_ADS, self.sample_ad)
        
        # İçeriklere reklam ekle
        content_mix = await self.model.insert_ads(self.sample_contents, 'test_user')
        
        # Test et
        self.assertIsInstance(content_mix, list)
        self.assertGreater(len(content_mix), len(self.sample_contents))
        
        # Reklam içeriklerini kontrol et
        ad_contents = [content for content in content_mix if content.get('is_ad', False)]
        self.assertGreater(len(ad_contents), 0)
        
        # Reklam metriklerini kontrol et
        ad_ref = self.model.firebase.db.collection(COLLECTION_ADS).document(self.sample_ad['id'])
        ad_data = await ad_ref.get()
        ad_data = ad_data.to_dict()
        
        self.assertGreater(ad_data['metrics']['impression_count'], 0)

    def tearDown(self):
        """Test sonrası temizlik"""
        # Test reklamını sil
        asyncio.run(self.model.firebase.delete_document(COLLECTION_ADS, self.sample_ad['id']))
        
        # Test metriklerini temizle
        asyncio.run(self.model.firebase.delete_collection(COLLECTION_AD_METRICS))

if __name__ == '__main__':
    unittest.main() 