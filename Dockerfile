
# Use official lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for XGBoost/Pandas)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY main.py .
COPY models_advanced/ ./models_advanced/

# Expose Port (Cloud Run defaults to 8080)
EXPOSE 8080

# Run Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
