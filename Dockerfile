# ── PDF Doctor Bot — Dockerfile ────────────────────────────────────────────
# GitHub: @SerenaXdev
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libtesseract-dev \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    wget \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Download Handwriting Fonts ───────────────────────────────────────────────
RUN mkdir -p fonts

# Caveat
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf" \
    -O fonts/Caveat.ttf || \
    wget -q "https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Regular.ttf" \
    -O fonts/Caveat.ttf || true

# Dancing Script
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-Regular.ttf" \
    -O fonts/DancingScript.ttf || true

# Kalam
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf" \
    -O fonts/Kalam.ttf || true

# Pacifico
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf" \
    -O fonts/Pacifico.ttf || true

# Satisfy
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf" \
    -O fonts/Satisfy.ttf || true

# Shadows Into Light
RUN wget -q "https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight-Regular.ttf" \
    -O fonts/ShadowsIntoLight.ttf || true

# ── Install Python packages ──────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ──────────────────────────────────────────────────────────────
COPY . .

# Create data directory for SQLite
RUN mkdir -p data

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]
