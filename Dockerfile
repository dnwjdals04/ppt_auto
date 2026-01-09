FROM python:3.11-slim

# 기본 환경변수
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Chromium + driver + 한글 폰트(가사/성경 표시 깨짐 방지)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

EXPOSE 8000

# ✅ app.py 안에 app = create_app() 이므로 "app:app"
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
