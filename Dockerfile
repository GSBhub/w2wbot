FROM ghcr.io/astral-sh/uv:python3.11-alpine

RUN apk add --no-cache gcc musl-dev

WORKDIR /w2wbot

COPY pyproject.toml .
RUN uv sync --no-dev --no-cache

COPY *.py .

ENTRYPOINT ["uv", "run", "python", "w2wbot.py"]
