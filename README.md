# Duygu Tabanlı Öneri Sistemi

Bu proje, kullanıcıların duygusal etkileşimlerine dayalı olarak içerik ve reklam önerileri sunan bir API servisidir.

## Özellikler

- Duygu tabanlı içerik önerileri
- Akıllı reklam yerleştirme
- Kullanıcı duygu desenlerinin analizi
- Firebase entegrasyonu
- RESTful API

## Kurulum

1. Gereksinimleri yükleyin:
```bash
pip install -r src/requirements.txt
```

2. Environment değişkenlerini ayarlayın:
- `.env.example` dosyasını `.env` olarak kopyalayın
- Firebase kimlik bilgilerinizi base64 formatında `FIREBASE_CREDENTIALS` değişkenine ekleyin

3. Uygulamayı başlatın:
```bash
cd src
python app.py
```

## API Endpoint'leri

### GET /api/recommendations/{user_id}
Kullanıcıya özel içerik ve reklam önerileri döndürür.

### POST /api/track_interaction
Kullanıcı etkileşimlerini kaydeder.

Örnek istek:
```json
{
    "userId": "user123",
    "postId": "post456",
    "interactionType": "like",
    "emotion": "Neşe (Joy)",
    "confidence": 0.9
}
```

## Railway Deployment

1. Railway CLI'ı yükleyin
2. Environment değişkenlerini Railway dashboard'dan ayarlayın:
   - `FIREBASE_CREDENTIALS`
   - `PORT` (Railway otomatik ayarlayacak)
3. Deploy edin:
```bash
railway up
```

## Lisans

MIT 