# GuideU — Performance Notes

How GuideU keeps the API fast, for the thesis performance chapter.

## Database access
- List endpoints use `select_related` / `prefetch_related` to avoid N+1 queries:
  - `catalog`: routes `select_related("region")`; guides and events prefetched.
  - `recommendations`: guide/route feeds select the related rows in one pass.
  - `workspace`: trips `prefetch_related("items")`; items `select_related`
    route/guide/package.
  - `chat`: threads `prefetch_related("messages")`; messages `select_related("sender")`.
- Foreign keys and frequently filtered columns are indexed (see each model's
  `Meta.indexes` and `db_index=True`).

## Caching (Redis)
- Exchange rates are cached for 6 hours and refreshed by a Celery Beat task,
  so the currency feature never blocks on the external rate API.
- The festival calendar (`/catalog/events/upcoming/`) caches its grouped result
  for 30 minutes — it only changes when an admin edits events.
- DRF throttling also rides on the Redis cache.

## Mobile
- All lists use `ListView.builder` (lazy), images use `cached_network_image`.
- Riverpod `autoDispose` providers release state when screens close.

## Load testing (how to reproduce)
With the stack running (`docker compose up -d`), a simple Locust profile can hit
the hot read endpoints:

```python
# locustfile.py
from locust import HttpUser, task, between

class GuideUUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def routes(self):
        self.client.get("/api/v1/catalog/routes/")

    @task(2)
    def festivals(self):
        self.client.get("/api/v1/catalog/events/upcoming/")
```

```bash
locust -f locustfile.py --headless -u 50 -r 10 --run-time 1m --host http://localhost
```

Record the request/sec and p95 latency here once captured on the deployed stack.
(Numbers are environment-specific, so they are measured on the demo deployment
rather than committed from a dev laptop.)
