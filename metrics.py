from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest
)
from aiohttp import web

COUNT_ACTIVE_USERS = Gauge("active_users", "Active user connections")
COUNT_REQUESTS = Counter("requests_total", "Total incoming requests")
COUNT_CONNECTIONS = Counter("connections_total", "Total connections created")
BYTE_SENT = Histogram("bytes_sent", "Bytes sent per request", buckets=(100, 500, 1000, 5000, 10000))
SERVICE_STARTS = Counter("service_starts_total","How many times this service has been started")

async def metrics(request):
    return web.Response(
        body=generate_latest(),
        headers={"Content-Type": "text/plain; version=1.0.0"}
    )

async def start_metrics_server(host: str, port:int):
    app = web.Application()
    app.router.add_get('/metrics', metrics)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
