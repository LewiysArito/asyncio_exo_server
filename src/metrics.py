from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest
)
from aiohttp import web

COUNT_ACTIVE_USERS = Gauge("echo_server_active_users", "Active user connections")
COUNT_REQUESTS = Counter("echo_server_requests_total", "Total incoming requests")
COUNT_CONNECTIONS = Counter("echo_server_connections_total", "Total connections created")
BYTE_RECEIVED = Histogram("echo_server_bytes_received_total", "Total bytes received by the server", buckets=(100, 500, 1000, 5000, 10000))
SERVICE_STARTS = Counter("echo_server_service_starts_total","How many times this service has been started")

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
