FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY truenas_bot ./truenas_bot
RUN pip install --no-cache-dir . && useradd --system --uid 568 --no-create-home bot
USER 568:568
ENTRYPOINT ["python", "-m", "truenas_bot"]

