from services.firebase_service import FirebaseService
import asyncio

async def test_firebase():
    try:
        firebase = FirebaseService()
        print("Firebase bağlantısı başarılı!")
        
        # Tüm postları getir
        posts = await firebase.get_all_posts()
        print(f"Toplam post sayısı: {len(posts)}")
        
        # Son 7 günün içeriklerini getir
        recent_content = await firebase.get_recent_content(days=7)
        print(f"Son 7 günün içerik sayısı: {len(recent_content)}")
        
        # Popüler içerikleri getir
        popular_content = await firebase.get_popular_content(days=30)
        print(f"Son 30 günün popüler içerik sayısı: {len(popular_content)}")
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_firebase()) 