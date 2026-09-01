# FASE 1 Testing Guide — Redis Streams + Workers

## Overview

FASE 1 replaces the two in-process asyncio schedulers (`linkedin_scheduler.py`, `task_scheduler.py`) with:
- **Redis Streams**: Persistent message queues
- **worker-linkedin**: Standalone process consuming `linkedin:scheduled-posts`
- **worker-tasks**: Standalone process consuming `bedrock:scheduled-tasks`

This guide walks through manual verification before prod deployment.

## Prerequisites

- Docker and docker-compose installed
- `.env` file configured with:
  - Database credentials (PostgreSQL)
  - AWS Bedrock keys (if testing task execution)
  - LinkedIn OAuth keys (if testing LinkedIn posts)
  - MinIO credentials

## Step 1: Bring up the full stack

```bash
cd /mnt/disco2/cjhirashi-data/proyectos/cjhirashi-career

# Start all services (includes new workers)
docker compose up redis worker-linkedin worker-tasks postgres api qdrant minio grafana loki promtail

# In another terminal, monitor Redis
docker exec redis_cache redis-cli
```

Expected output:
```
redis_cache  | 1:M 01 Sep 03:50:00.000 * Ready to accept connections
worker_linkedin | [INFO] Worker started, consuming from linkedin:scheduled-posts
worker_tasks    | [INFO] Worker started, consuming from bedrock:scheduled-tasks
```

## Step 2: Verify Redis connectivity

```bash
# Inside docker exec redis_cache redis-cli
> PING
PONG

> XLEN linkedin:scheduled-posts
(integer) 0

> XLEN bedrock:scheduled-tasks
(integer) 0
```

Both streams should exist and be empty.

## Step 3: Test LinkedIn Post Scheduling

### Create a LinkedIn post scheduled for the past (immediate publish via worker)

```bash
#!/bin/bash
USER_ID="usr-2"  # Your actual user ID
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password" | jq -r '.access_token')

# Schedule a post 60 seconds in the past (worker should pick it up immediately)
SCHEDULED_AT=$(date -u -d '-1 minute' +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST http://localhost:8001/linkedin/posts \
  -H "Authorization: Bearer $TOKEN" \
  -F "text=Test post from FASE 1 worker" \
  -F "scheduled_at=$SCHEDULED_AT"
```

### Verify the flow

#### In Redis:
```bash
docker exec redis_cache redis-cli XLEN linkedin:scheduled-posts
# Should see 1 (or more if you tested multiple times)

docker exec redis_cache redis-cli XREAD COUNT 1 STREAMS linkedin:scheduled-posts 0
# Should see message with post_id and scheduled_at
```

#### In worker-linkedin logs:
```bash
docker logs -f worker_linkedin
# Should see:
# [INFO] Enqueued LinkedIn post {post_id} to Redis stream
# [INFO] Published post {post_id} (msg {msg_id})
```

#### In database:
```bash
docker exec postgres_db psql -U career_admin -d career_db -c "
  SELECT id, status, linkedin_post_urn, published_at 
  FROM linkedin_posts 
  ORDER BY created_at DESC 
  LIMIT 1;
"
# Should show status=PUBLISHED, linkedin_post_urn populated, published_at recent
```

#### Idempotence test:
Create the same post again (same text, same scheduled_at).
- Worker should see it's already PUBLISHED and skip (no duplicate on LinkedIn)
- Check logs: "Post {id} already published, skipping"

## Step 4: Test Agent Task Scheduling

### Create a scheduled task

```bash
USER_ID="usr-2"
TOKEN=$(... get token from /auth/login ...)
SCHEDULED_AT=$(date -u -d '+2 minutes' +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST http://localhost:8001/agent-tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Test scheduled task\",
    \"description\": \"Verify FASE 1 worker can execute\",
    \"scheduled_at\": \"$SCHEDULED_AT\",
    \"assignee_type\": \"agent\",
    \"agent_profile_id\": \"l1-analyst\",
    \"priority\": \"medium\"
  }"
```

### Verify the flow

#### In Redis (wait for scheduled time):
```bash
docker exec redis_cache redis-cli XLEN bedrock:scheduled-tasks
# Should see 1

docker exec redis_cache redis-cli XREAD COUNT 1 STREAMS bedrock:scheduled-tasks 0
# Should see message with task_id
```

#### In worker-tasks logs (after scheduled_at time passes):
```bash
docker logs -f worker_tasks
# Should see:
# [INFO] Enqueued task {task_id} to Redis stream
# (worker waits until scheduled_at time)
# [INFO] Task {task_id} completed successfully
```

#### In database:
```bash
docker exec postgres_db psql -U career_admin -d career_db -c "
  SELECT id, status, execution_result, executed_at 
  FROM agent_system_tasks 
  ORDER BY created_at DESC 
  LIMIT 1;
"
# Should show status=done, execution_result populated, executed_at recent
```

## Step 5: Verify Idempotence

### LinkedIn idempotence:
- Manually add the same message to Redis twice:
  ```bash
  docker exec redis_cache redis-cli XADD linkedin:scheduled-posts "*" post_id=<existing_id> scheduled_at="2026-09-01T03:00:00Z"
  ```
- Watch worker logs: should see "Post {id} already published, skipping"

### Task idempotence:
- Manually update a task in Postgres to status=pending (after it executed)
- Manually add its message to Redis again
- Watch worker logs: should see task execution skipped because status != pending/failed

## Step 6: Test Worker Restart & Durability

### Kill worker-linkedin, then check that pending messages are still in Redis:
```bash
docker stop worker_linkedin
docker exec redis_cache redis-cli XLEN linkedin:scheduled-posts
# Should still show queued messages

docker start worker_linkedin
docker logs -f worker_linkedin
# Should resume processing from where it left off (XREADGROUP with > only reads NEW messages,
# but XPENDING will requeue failed ones on restart)
```

## Step 7: Verify No Duplication with Old Scheduler

With the old scheduler disabled (lines commented in `app.py`), verify:

```bash
# API process does NOT include scheduler loops
docker logs -f cjhirashi-career-api
# Should NOT see "LinkedIn post scheduler started"
# Should NOT see "Agent task scheduler started"

# Only workers should process messages
docker logs -f worker_linkedin | grep "Published post"
docker logs -f worker_tasks | grep "Task .* completed"
```

## Step 8: Monitoring & Alerting (Observability)

Check Grafana/Loki dashboards (if deployed):
```bash
# Loki URL: http://localhost:3100
# Grafana URL: http://localhost:3000 (admin/admin)
```

- Stream size:  `docker exec redis_cache redis-cli XLEN linkedin:scheduled-posts`
- Pending messages: `docker exec redis_cache redis-cli XPENDING linkedin:scheduled-posts linkedin-workers`
- Consumer lag: `docker exec redis_cache redis-cli XINFO CONSUMERS linkedin:scheduled-posts linkedin-workers`

## Rollback Plan

If workers fail and you need to revert to in-process schedulers:

### Temporary rollback (restart API with old schedulers):
```bash
# Edit src/app.py: uncomment lines 81-84 and 90-91
# Restart API
docker compose restart api
docker logs -f cjhirashi-career-api
# Should see "LinkedIn post scheduler started" again
```

### Permanent rollback (git):
```bash
git revert 6ac222e  # Revert "FASE 1: Redis Streams + Workers (base structure)"
docker compose build api
docker compose restart api
```

## Checklist for Production Deployment

- [ ] All smoke tests pass locally
- [ ] No duplicate posts on LinkedIn (XACK confirms consumption)
- [ ] No duplicate task executions (task.status prevents re-run)
- [ ] Worker logs show clean startup and message consumption
- [ ] Redis XPENDING is empty (no stuck messages)
- [ ] Task worker completes within expected time (Bedrock execution + DB updates)
- [ ] LinkedIn worker completes < 30s per post (API rate limits)
- [ ] 24h staging test with actual LinkedIn account
- [ ] Monitoring configured: Redis stream size, worker lag
- [ ] On-call runbook updated with worker troubleshooting steps

## Common Issues & Debugging

### "Worker not consuming messages"
- [ ] Check Redis is healthy: `docker logs redis_cache`
- [ ] Verify stream exists: `docker exec redis_cache redis-cli XLEN linkedin:scheduled-posts`
- [ ] Check consumer group: `docker exec redis_cache redis-cli XINFO GROUPS linkedin:scheduled-posts`
- [ ] Check for errors: `docker logs worker_linkedin | grep -i error`

### "Message stuck in XPENDING"
- [ ] Message delivery failed; check worker logs
- [ ] Manual retry: `docker exec redis_cache redis-cli XCLAIM linkedin:scheduled-posts linkedin-workers 0 <msg_id>`
- [ ] Or manually set post status in DB and retry

### "Duplicate posts published"
- [ ] XACK not called; check worker logs for "XACK" entries
- [ ] Verify idempotence: both LinkedIn API and our logic check DB state first

### "Worker crashes on startup"
- [ ] Check Python import errors: `docker logs worker_linkedin | head -50`
- [ ] Verify `.env` has all required keys
- [ ] Verify database is accessible from worker container

---

**Next Phase:** FASE 2 — Centralizar acceso a datos (refactor DB repositories)
