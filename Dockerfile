# Sample Dockerfile for environment consistency
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["pytest", "--maxfail=5", "--disable-warnings"]
