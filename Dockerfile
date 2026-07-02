FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    libtiff-dev \
    libopenjp2-7-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
