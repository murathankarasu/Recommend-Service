import asyncio
import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(project_root)

from services.firebase_service import FirebaseService

# Eski duygu kategorileri
OLD_EMOTIONS = ['mutlu', 'üzgün', 'kızgın', 'korkmuş', 'şaşkın', 'nötr']

async def delete_old_posts():
    firebase_service = FirebaseService()
    
    # Tüm postları getir
    posts = await firebase_service.get_all_posts()
    deleted_count = 0
    
    # Sadece eski duygu kategorilerine sahip postları sil
    for post in posts:
        if post.get('emotion') in OLD_EMOTIONS:
            await firebase_service.delete_post(post['id'])
            print(f"Eski post silindi: {post['id']} (Duygu: {post['emotion']})")
            deleted_count += 1
    
    print(f"\nToplam {deleted_count} eski post silindi!")

if __name__ == "__main__":
    asyncio.run(delete_old_posts()) 