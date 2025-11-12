# Gebruik officiële Streamlit image (bewezen op DO)
FROM python:3.12-slim

# Werkdirectory
WORKDIR /app

# Kopieer bestanden
COPY requirements.txt .
COPY brilfit_ai.py .

# Installeer alleen wat nodig is
RUN pip install --no-cache-dir -r requirements.txt

# Poort openen
EXPOSE 8080

# Start Streamlit op de juiste poort
CMD ["streamlit", "run", "brilfit_ai.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
