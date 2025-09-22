FROM python:3.11-alpine

WORKDIR /app

# System dependencies
RUN apk add --no-cache curl

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY clicker.py .

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["python", "clicker.py"]
