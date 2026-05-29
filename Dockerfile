FROM python:3.12-slim

WORKDIR /app

# Install deps first so this layer is cached between code-only changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Render injects PORT at runtime; fall back to 8000 locally
ENV PORT=8000

EXPOSE $PORT

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1"]
