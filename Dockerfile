FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN python -m pip install --upgrade pip \
    && pip install -e packages/gennai_app_kit \
    && pip install -e packages/gennai_evals \
    && pip install -e packages/gennai_cli \
    && pip install -e packages/gennai_local_runner \
    && pip install -e packages/gennai_red_team_lite \
    && pip install -e packages/gennai_observability \
    && pip install fastapi uvicorn pytest pyyaml jsonschema

CMD ["uvicorn", "apps.easy_japanese_rewriter.app:app", "--host", "0.0.0.0", "--port", "8000"]
