# Phase 12 — Production deployment

## Deployment architecture

`docker-compose.production.yml` runs the backend with PostgreSQL 16 + pgvector
on a private network. Caddy is the only public service and terminates HTTPS for
`APP_DOMAIN`, forwarding traffic to the backend over the internal edge network.
The backend image runs as the non-root `app` user and applies Alembic migrations
before startup.

## Required environment

Copy `backend/.env.example` to `backend/.env` and set production values. Set
`APP_DOMAIN`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and a
random `SECRET_KEY` of at least 32 characters through an uncommitted
`.env`/secret manager. Never commit credentials or service-account files.

Start and validate:

```sh
docker compose --env-file .env -f docker-compose.production.yml up -d --build
curl -fsS https://$APP_DOMAIN/health
curl -fsS https://$APP_DOMAIN/ready
```

## Operations

- **Logging:** container stdout and request-correlation logs are the canonical
  stream; forward them to the host/provider log collector.
- **Monitoring:** probe `/health` for liveness, `/ready` for database readiness,
  and scrape `/metrics` from a private network only.
- **Backups:** run `POSTGRES_DB=... POSTGRES_USER=... BACKUP_DIR=... pg_dump`
  using [`scripts/backup-postgres.sh`](../scripts/backup-postgres.sh), encrypt
  and copy dumps to durable off-host storage, and regularly test restores.
- **Security:** use a secrets manager, restrict database access to the private
  network, keep Caddy's automatic certificates current, review dependency
  audits, and rotate credentials.

The repository contains deployment automation and safe defaults, but it is not
itself a hosted production deployment until an operator supplies the domain,
TLS DNS, secrets, backup storage, and monitoring destination.
