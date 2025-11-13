FROM python:3.12-slim

# Installeer system dependencies voor OpenCV (libGL + video support)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "brilfit_ai.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
