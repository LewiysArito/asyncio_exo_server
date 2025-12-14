from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest
)
from aiohttp import web
import psutil
import time
import threading
from src.settings import logger

COUNT_ACTIVE_USERS = Gauge("echo_server_active_users", "Active user connections")
COUNT_REQUESTS = Counter("echo_server_requests_total", "Total incoming requests")
COUNT_CONNECTIONS = Counter("echo_server_connections_total", "Total connections created")
BYTE_RECEIVED = Histogram("echo_server_bytes_received_total", "Total bytes received by the server", buckets=(10, 25, 50, 100))
SERVICE_STARTS = Counter("echo_server_service_starts_total","How many times this service has been started")
CPU_USAGE = Gauge('echo_server_app_cpu_percent', 'CPU usage percent')
MEMORY_USAGE = Gauge('echo_server_app_memory_bytes', 'Memory usage in bytes')

async def metrics(request):
    return web.Response(
        body=generate_latest(),
        headers={"Content-Type": "text/plain; version=1.0.0"}
    )

def collect_system_metrics():
    proc = psutil.Process()
    proc.cpu_percent()
    while True:    
        cpu_percent = proc.cpu_percent(interval=0.5)
        CPU_USAGE.set(cpu_percent)
        memory_usage = psutil.Process().memory_info().rss
        MEMORY_USAGE.set(memory_usage)
        time.sleep(0.5)

async def start_metrics_server(host: str, port:int):
    app = web.Application()
    app.router.add_get('/metrics', metrics)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    thread = threading.Thread(target=collect_system_metrics, daemon=True)
    thread.start()
    await site.start()

    return runner