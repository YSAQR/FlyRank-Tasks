FROM python:3.11-slim

WORKDIR /app

# Install build tools and libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

EXPOSE 8000

CMD ["uvicorn", "CurdTask:app", "--host", "0.0.0.0", "--port", "8000"]
