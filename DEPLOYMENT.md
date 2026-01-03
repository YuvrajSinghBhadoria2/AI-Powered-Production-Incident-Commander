# Production Deployment Guide: AI Incident Commander

This guide provides instructions for deploying the AI Incident Commander in a production-ready environment.

## Prerequisites
- A cloud VPS or container orchestration platform (e.g., AWS, GCP, Azure, Railway, Render).
- Docker and Docker Compose installed on the host.
- A PostgreSQL database instance (included in Docker Compose as a starting point).
- API Keys for **Groq**, **Pinecone**, and a custom **API_KEY** for your system.

## 1. Environment Configuration
Create a `.env` file in the root directory (or set these in your CI/CD provider):

### Backend Configuration (`backend/.env`)
```env
# Infrastructure
DATABASE_URL=postgresql://user:password@db_host:5432/commander
API_KEY=your_secure_random_api_key

# AI Services
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=incident-commander
```

### Frontend Configuration (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
X_API_KEY=your_secure_random_api_key
```

## 2. Deployment via Docker Compose
The simplest way to deploy is using the provided `docker-compose.yml`.

```bash
# Build and start services in detached mode
docker-compose up -d --build
```

This will spin up:
- **Backend**: FastAPI on port 8000 (proxied via Gunicorn).
- **Frontend**: Next.js on port 3000.
- **Database**: PostgreSQL on port 5432.

## 3. Production Hardening Checklist
- [ ] **HTTPS**: Use a reverse proxy like Nginx or Traefik with Let's Encrypt for SSL.
- [ ] **Auth**: Ensure `API_KEY` is long and random.
- [ ] **Scaling**: For high traffic, increase Gunicorn workers (`-w`) and use a managed PostgreSQL service (e.g., RDS).
- [ ] **Monitoring**: Integrate with Prometheus/Grafana using the OTel ingestion endpoint.

## 4. CI/CD
A GitHub Actions workflow is provided in `.github/workflows/docker-publish.yml` to automatically verify builds on every push to `main`.

## 5. Ingesting Real Data
Configure your services to send OTel-compliant JSON to the `/ingest/otel` endpoint with the `X-API-Key` header.
