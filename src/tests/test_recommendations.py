import requests
import json
import time

# Kullanıcı ID'si
user_id = "isRKPOpG4zVFmULHJjrsvY8t1Nb2"

# API adresi
url = f"http://0.0.0.0:8000/api/recommendations/{user_id}"

print(f"[INFO] API'ya istek atılıyor: {url}")

# 1. İlk feed'i al ve postId'leri kaydet
response = requests.get(url, headers={"Content-Type": "application/json"})
data = response.json()
feed_post_ids = [rec["id"] for rec in data.get("recommendations", []) if "id" in rec]

print("[INFO] İlk feed postId'leri:", feed_post_ids)
print("[INFO] İlk emotion_pattern:", data.get("emotion_pattern"))

# 2. Hiçbir etkileşim göndermeden tekrar aynı feed için istek at (stretching tetiklenmeli)
time.sleep(2)  # Simülasyon için kısa bir bekleme
response2 = requests.get(url, headers={"Content-Type": "application/json"})
data2 = response2.json()
print("[INFO] İkinci feed emotion_pattern:", data2.get("emotion_pattern"))

# 3. Stretching olup olmadığını kontrol et
if data2.get("emotion_pattern") != data.get("emotion_pattern"):
    print("[SUCCESS] Stretching devreye girdi!")
else:
    print("[WARN] Stretching devreye girmedi. shown_post_ids ve etkileşim kontrolünü gözden geçirin.")

# Öneri detaylarını ayrı ayrı göster
if response.status_code == 200 and "recommendations" in data:
    print("\n[INFO] Öneri Listesi:")
    for i, rec in enumerate(data["recommendations"], 1):
        print(f"--- {i}. Öneri ---")
        for k, v in rec.items():
            print(f"{k}: {v}")
        print()
else:
    print("[WARN] Öneri listesi bulunamadı veya hata oluştu.") 