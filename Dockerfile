FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    stockfish \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 786

ENTRYPOINT ["python", "app/main.py"]
