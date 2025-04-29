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

---

# Algoritma ve Fonksiyonların Detaylı Açıklaması

Bu bölümde, öneri sisteminin tüm ana algoritmaları ve yardımcı modülleri detaylı olarak açıklanmıştır. Her fonksiyonun amacı, parametreleri, işleyişi ve örnek akışları uzun uzun anlatılmıştır.

## 1. Ana Akış: Kullanıcıya Öneri Sunma

### `GET /api/recommendations/<user_id>`
Bu endpoint, bir kullanıcıya özel içerik ve reklam önerileri döndürür. Akış şu şekildedir:

1. **Kullanıcı Etkileşimleri Getirilir:**
   - `firebase.get_user_interactions(user_id)` ile kullanıcının geçmiş etkileşimleri çekilir.
   - Eğer hiç etkileşim yoksa cold start algoritması devreye girer.

2. **İçerik Havuzu Getirilir:**
   - `firebase_post.get_all_posts()` ile tüm içerikler alınır.

3. **Duygu Deseni Analizi:**
   - `emotion_analyzer.analyze_pattern(user_interactions, user_id)` fonksiyonu ile kullanıcının duygusal eğilimleri çıkarılır.
   - Sonuç: Her duygu için 0-1 arası bir oran.

4. **Kullanıcıya Gösterilen İçeriklerin Filtrelenmesi:**
   - `get_recent_shown_post_ids(user_interactions)` ile son gösterilen içerikler belirlenir.

5. **Kişiselleştirilmiş İçerik Karışımı:**
   - `content_recommender.get_content_mix(...)` fonksiyonu ile kullanıcının duygu desenine ve geçmişine göre içerik karışımı oluşturulur.

6. **Reklamların Eklenmesi:**
   - `ad_manager.insert_ads(content_mix, user_id)` ile uygun yerlere reklamlar eklenir.

7. **A/B Test ve Loglama:**
   - `log_recommendation_event(...)` ile öneri ve parametreler loglanır.

8. **Yanıtın Dönülmesi:**
   - Sonuç, öneriler ve duygu deseni ile birlikte döndürülür.

---

## 2. Cold Start Algoritması

### `get_cold_start_content(all_contents, emotion_categories, limit)`
Hiç etkileşimi olmayan kullanıcılar için çeşitli ve popüler içeriklerden oluşan bir öneri listesi oluşturur.

- **Her duygudan en az 1 içerik** eklenir (varsa).
- Kalan slotlar, popülerlik (beğeni + yorum + görüntülenme) puanına göre doldurulur.
- Sonuç karıştırılır ve limit kadar içerik döndürülür.

**Parametreler:**
- `all_contents`: Tüm içeriklerin listesi (dict).
- `emotion_categories`: Duygu kategorilerinin listesi.
- `limit`: Döndürülecek içerik sayısı.

**Örnek Akış:**
1. Her duygudan rastgele bir içerik seç.
2. Kalan slotları popüler içeriklerle doldur.
3. Sonuçları karıştır ve döndür.

---

## 3. Duygu Deseni Analizi

### `analyze_pattern(user_interactions, user_id)`
Kullanıcının geçmiş etkileşimlerinden, hangi duygulara daha çok tepki verdiğini analiz eder.

- Her etkileşimdeki duyguya ağırlık verilir.
- Sonuçta, her duygu için 0-1 arası bir oran elde edilir.
- Bu oranlar, öneri algoritmasında içeriklerin sıralanmasında kullanılır.

**Parametreler:**
- `user_interactions`: Kullanıcının etkileşim listesi.
- `user_id`: Kullanıcı ID'si.

**Örnek:**
- Kullanıcı 10 etkileşimin 6'sında "Neşe", 4'ünde "Aşk" seçmişse:
  - `{"Neşe": 0.6, "Aşk": 0.4, ...}`

---

## 4. İçerik Karışımı ve Sıralama

### `get_content_mix(contents, emotion_pattern, limit, shown_post_ids)`
Kullanıcının duygu desenine ve geçmişte gördüğü içeriklere göre, yeni bir içerik karışımı oluşturur.

- Daha önce gösterilen içerikler hariç tutulur.
- İçerikler, kullanıcının baskın duygularına göre ağırlıklandırılır.
- Skoru aynı olan içerikler için küçük bir rastgelelik eklenir (`shuffle_same_score`).
- Sonuç, limit kadar içerik olacak şekilde döndürülür.

**Parametreler:**
- `contents`: Tüm içerikler.
- `emotion_pattern`: Kullanıcının duygu deseni.
- `limit`: Döndürülecek içerik sayısı.
- `shown_post_ids`: Daha önce gösterilen içeriklerin ID'leri.

---

## 5. Yardımcı Modüller

### `user_history_utils.py`
- Kullanıcıya son gösterilen içeriklerin ID'lerini döndürür.
- Tekrarlı içeriklerin önüne geçmek için kullanılır.

### `shuffle_utils.py`
- Skoru aynı olan içerikleri kendi aralarında karıştırır.
- Öneri listesinin monoton olmasını engeller.

### `date_utils.py`
- Farklı timestamp formatlarını güvenli şekilde parse eder ve UTC'ye normalize eder.
- Tarih işlemlerinde hata riskini azaltır.

### `ab_test_logger.py`
- Öneri algoritmasında yapılan A/B testlerinin ve parametrelerin loglanmasını sağlar.
- Sonuçların analizinde kullanılır.

### `cold_start_utils.py`
- Cold start (yeni kullanıcı) için öneri karışımı oluşturur.
- Duygu çeşitliliği ve popülerlik dengesini sağlar.

---

## 6. Reklam Yerleştirme

### `ad_manager.insert_ads(content_mix, user_id)`
- İçerik karışımına, kullanıcının duygu desenine ve ilgi alanlarına uygun reklamlar ekler.
- Reklamlar, belirli aralıklarla ve öncelik sırasına göre yerleştirilir.
- Her reklamın hedef duyguları ve önceliği dikkate alınır.

---

## 7. Kullanıcı Etkileşimi Kaydı

### `POST /api/track_interaction`
- Kullanıcı bir içerikle etkileşime geçtiğinde (beğeni, yorum, duygu seçimi vb.) bu endpoint çağrılır.
- Etkileşim Firebase'e kaydedilir.
- İçerik etkileşim istatistikleri güncellenir.

**Parametreler:**
- `userId`: Kullanıcı ID'si
- `postId`: İçerik ID'si
- `interactionType`: Etkileşim türü (like, comment, view, emotion, vs.)
- `emotion`: Kullanıcının seçtiği duygu
- `confidence`: Duygu tespiti güven skoru

---

## 8. A/B Test Mantığı

- Kullanıcılar rastgele veya belirli kurallara göre farklı algoritma/parametre varyantlarına atanabilir.
- Her öneri isteğinde, hangi varyantın kullanıldığı ve sonuçları loglanır.
- Sonuçlar analiz edilerek, en iyi performans gösteren algoritma/parametreler belirlenir.

---

## 9. Algoritma Akışı (Özet)

1. Kullanıcıdan öneri isteği gelir.
2. Kullanıcı etkileşimleri ve içerik havuzu çekilir.
3. Eğer hiç etkileşim yoksa cold start algoritması çalışır.
4. Varsa, duygu deseni analiz edilir ve içerik karışımı oluşturulur.
5. Reklamlar uygun yerlere eklenir.
6. Sonuç ve parametreler loglanır.
7. Öneri listesi ve duygu deseni API yanıtı olarak döndürülür.

---

## 10. Geliştiriciye Notlar

- Her fonksiyon ve modül, kolayca test edilebilecek şekilde bağımsız yazılmıştır.
- Yardımcı modüller, ana algoritmalardan bağımsız olarak başka projelerde de kullanılabilir.
- Kodun tamamı Python 3.8+ ile uyumludur.
- Firebase entegrasyonu için environment değişkenleri doğru ayarlanmalıdır.

---

## 11. Dinamik Duygu Deseni ve Esnetme Mekanizması

Öneri sistemi, kullanıcının etkileşimlerine göre sürekli olarak kendini günceller ve kişiselleştirir. Bu süreç iki ana akıştan oluşur:

### a) Kişiselleşme (Etkileşim Oldukça)
- Kullanıcı önerilen feeddeki içeriklere **etkileşim** (like, comment, emotion) verdikçe, bu etkileşimler analiz edilir.
- Her yeni etkileşimde, kullanıcının **duygu deseni (emotion_pattern)** yeniden hesaplanır.
- Örneğin, kullanıcı "Neşe (Joy)" içeriklerine daha çok like verirse, "Neşe" oranı artar; "Öfke (Anger)" içeriklerine hiç etkileşim vermezse, "Öfke" oranı azalır.
- Sonraki feedlerde, öneriler bu güncel duygu desenine göre ağırlıklandırılır ve giderek daha kişisel hale gelir.

### b) Esnetme (Etkileşim Olmazsa)
- Eğer kullanıcı, önerilen feeddeki içeriklere **hiçbir anlamlı etkileşim** (like, comment, emotion) vermezse, sistem otomatik olarak esnetme mantığını devreye alır.
- Esnetme mantığında:
  - Baskın duygu oranı %50'ye çekilir.
  - Diğer tüm duygular kalan %50'yi eşit paylaşır.
- Böylece, kullanıcı ilgisiz kaldığında sistem otomatik olarak çeşitliliği artırır ve tekdüzelikten kurtarır.
- Kullanıcı tekrar etkileşim vermeye başladığında, sistem tekrar kişiselleşmiş pattern'a döner.

**Kısacası:**
- Kullanıcı etkileşim verdikçe yüzdeler değişir ve öneri sistemi giderek daha akıllı ve kişisel çalışır.
- Kullanıcı ilgisiz kalırsa, sistem otomatik olarak çeşitliliği artırır.

---

Her türlü katkı, öneri ve hata bildirimi için lütfen issue açın veya pull request gönderin.

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