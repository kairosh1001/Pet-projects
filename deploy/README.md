# VPS Deployment Notes

This is the intended low-cost v1 deployment path:

1. Rent a small VPS, such as Hetzner CX23 if pricing is acceptable.
2. Install Docker and the Docker Compose plugin.
3. Clone this repository onto the server.
4. Copy `.env.example` to `.env` and adjust values if needed.
5. Start the app with Docker Compose.
6. Add cron jobs for daily and weekly refreshes.
7. Add Caddy/HTTPS after the app works by server IP.

## First Server Run

From the repository directory:

```bash
cp .env.example .env
docker compose build
docker compose up -d app
docker compose ps
curl http://127.0.0.1:8000/health
```

Before exposing the app publicly, edit `.env` and replace `ADMIN_TOKEN=change-me`
with a private value.

If the server firewall allows port 8000, the app can be tested by IP first:

```text
http://SERVER_IP:8000
```

## Refresh Commands

Daily refresh:

```bash
docker compose --profile tools run --rm refresh \
  python scripts/refresh_listings.py --kind daily --pages 50
```

Weekly refresh:

```bash
docker compose --profile tools run --rm refresh \
  python scripts/refresh_listings.py --kind weekly --pages 200
```

Small smoke test:

```bash
docker compose --profile tools run --rm refresh \
  python scripts/refresh_listings.py --kind manual --pages 1 --max-listings 3 --min-delay 0 --max-delay 0
```

Admin endpoint smoke test:

```bash
curl -X POST http://127.0.0.1:8000/refresh-listings \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -d '{"kind":"manual","pages":1,"max_listings":3,"min_delay":0,"max_delay":0}'
```

## Cron Example

Edit crontab:

```bash
crontab -e
```

Example entries:

```cron
# Daily shallow refresh at 03:00.
0 3 * * * cd /opt/krisha && docker compose --profile tools run --rm refresh python scripts/refresh_listings.py --kind daily --pages 50 >> logs/daily-refresh.log 2>&1

# Weekly deeper refresh on Sunday at 04:00.
0 4 * * 0 cd /opt/krisha && docker compose --profile tools run --rm refresh python scripts/refresh_listings.py --kind weekly --pages 200 >> logs/weekly-refresh.log 2>&1
```

Replace `/opt/krisha` with the actual repository path.

## Caddy/HTTPS

Use `deploy/Caddyfile.example` after a domain points to the VPS.

Without a domain, keep testing by IP and port first.

## Runtime Data

SQLite data is stored in:

```text
./data/krisha.sqlite3
```

Back this file up before rebuilding or moving servers. The Compose file mounts `./data` into the app container, so normal container rebuilds should not delete it.
