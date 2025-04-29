FROM python:3.8-slim

WORKDIR /app

# Önce pip'i güncelle
RUN pip install --upgrade pip

# Sonra bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Port ayarları
ENV PORT=8080
EXPOSE $PORT

# Uygulamayı başlat
CMD gunicorn --bind 0.0.0.0:$PORT app:app 