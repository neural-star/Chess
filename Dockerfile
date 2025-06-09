FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    librsvg2-bin \
    stockfish \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/app.py"]
