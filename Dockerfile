# FastAPI backend image.
#
# The index is built AT IMAGE BUILD TIME (RUN python ingest.py): this bakes
# both the FAISS index and the sentence-transformers model download into an
# image layer, so containers start serving immediately with no cold model
# download and no runtime dependency on huggingface.co.
#
# Honest size note: torch (pulled in by sentence-transformers) makes this
# image ~2 GB. Acceptable for a personal project; slimming it would mean
# swapping to an ONNX-runtime embedder, which is out of scope here.
#
# Secrets (GROQ_API_KEY, JWT_SECRET_KEY, credentials) are NOT copied in —
# .dockerignore excludes .env; docker-compose injects them at runtime.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag/ rag/
COPY api/ api/
COPY docs/ docs/
COPY ingest.py .

RUN python ingest.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
