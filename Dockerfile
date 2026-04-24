FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e packages/gennai_app_kit fastapi uvicorn
EXPOSE 8000
CMD ["uvicorn", "apps.easy_japanese_rewriter.app:app", "--host", "0.0.0.0", "--port", "8000"]
