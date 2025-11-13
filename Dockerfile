FROM python:3.12-buster  # Buster voor betere libGL compat (niet slim)

# Installeer alle OpenCV dependencies (volledige fix uit SO/GitHub 2025)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    libgomp1 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "brilfit_ai.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
