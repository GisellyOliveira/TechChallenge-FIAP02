FROM python:3.12-slim AS build
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home --uid 10001 radar
WORKDIR /app
COPY --from=build /install /usr/local
COPY config ./config
COPY sql ./sql
USER radar
ENTRYPOINT ["radar"]
