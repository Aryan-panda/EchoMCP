FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    MODELS_DIR=/app/models \
    VOICES_DIR=/app/voices \
    OUTPUT_DIR=/app/output \
    PYTHONPATH="/app/CosyVoice:/app"

# Install system audio, compiling, and git tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ffmpeg \
    sox \
    libsox-dev \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA 12.1 support
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install core app dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone official CosyVoice engine for native instruction-following voice cloning
RUN git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git /app/CosyVoice && \
    cd /app/CosyVoice && \
    pip install --no-cache-dir -r requirements.txt || true && \
    pip install --no-cache-dir -e . || true

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

