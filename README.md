# API Rate Limiting & Gateway System

A lightweight API gateway similar to Kong, built with FastAPI, Redis, and React.

## Features

- **API Key Authentication** – Validate requests via `X-API-Key` header
- **Rate Limiting** – Per-user sliding window rate limits (Redis-backed)
- **Request Logging** – All requests logged for analytics
- **Caching** – GET response caching with configurable TTL
- **Reverse Proxy** – Route requests to backend services
- **Analytics Dashboard** – React dashboard for real-time metrics

## Tech Stack

- **FastAPI** – Gateway backend
- **Redis** – Rate limit counters, caching, request logs
- **Docker** – Containerized deployment
- **React** – Analytics dashboard

## Quick Start with Docker

```bash
# Start all services
docker compose up -d

# Gateway:     http://localhost:8000
# Dashboard:    http://localhost:3000
# Redis:        localhost:6379
```

## Usage

### Making requests through the gateway

All proxied requests require an API key:

```bash
# Using httpbin.org as default upstream
curl -H "X-API-Key: dev-key-12345" http://localhost:8000/get
curl -H "X-API-Key: dev-key-12345" http://localhost:8000/status/200
```

### Health & metrics

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Configuration

Environment variables (or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `UPSTREAM_URL` | `http://httpbin.org` | Backend service to proxy to |
| `API_KEYS` | (empty) | Comma-separated valid API keys. Empty = allow all (dev) |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window in seconds |
| `CACHE_TTL_SECONDS` | `300` | Cache TTL for GET responses |

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Redis

### Gateway

```bash
cd gateway
pip install -r requirements.txt

# Start Redis (Docker or local)
# docker run -d -p 6379:6379 redis:7-alpine

# Run gateway (from project root)
cd ..
uvicorn gateway.main:app --reload --port 8000
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard runs at http://localhost:5173 and proxies `/api` to the gateway.

## Project Structure

```
├── gateway/           # FastAPI gateway
│   ├── main.py        # App entry, middleware
│   ├── auth.py        # API key validation
│   ├── rate_limit.py  # Redis sliding-window rate limiting
│   ├── cache.py       # Response caching
│   ├── proxy.py       # Reverse proxy
│   ├── logging_middleware.py
│   └── redis_client.py
├── dashboard/         # React analytics UI
├── docker-compose.yml
└── README.md
```
