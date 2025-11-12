FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY brilfit_ai.py .

# Expose port
EXPOSE 8080

# Run Streamlit (headless for DO, no CORS/XSRF issues)
CMD ["streamlit", "run", "brilfit_ai.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
