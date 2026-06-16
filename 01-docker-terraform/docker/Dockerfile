FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked
COPY /01-docker-terraform/docker/ingest_data.py ./
ENTRYPOINT ["python", "ingest_data.py"]