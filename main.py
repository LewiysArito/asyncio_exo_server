import socket
import asyncio
import signal

import settings
from metrics import (
    COUNT_CONNECTIONS,
    SERVICE_STARTS,
    start_metrics_server,
    BYTE_SENT,
    COUNT_ACTIVE_USERS
)
from settings import logger
from asyncio import AbstractEventLoop
from typing import List
from schemas import EchoServerSettings

class EchoServer:
    def __init__(self, event_loop: AbstractEventLoop, settings: EchoServerSettings):
        self.event_loop = event_loop
        self.echo_tasks: List[asyncio.Task] = []
        self.settings = settings
        self.listener_task: asyncio.Task | None = None
        self.server_socket: socket.socket | None = None

    async def echo(self, connection: socket.socket):
        try:
            while True:
                data = await self.event_loop.sock_recv(connection, 1024)
                if data in (b"\r\n", b"\xff\xfb\x06"):
                    break
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info(f"Connection close {connection}")
            COUNT_ACTIVE_USERS.dec(1)
            connection.close()

    def shutdown(self, signame: str):
        logger.info(f"Received signal {signame}. Shutting down...")
        self.event_loop.create_task(self.close_and_stop())

    async def connection_listener(self, server_socket: socket.socket):
        while self.event_loop.is_running():
            try:
                connection, address = await self.event_loop.sock_accept(server_socket)
            except (asyncio.CancelledError, OSError):
                break
            
            connection.setblocking(False)
            logger.info(f"New connection from {address}")
            COUNT_CONNECTIONS.inc(1)
            COUNT_ACTIVE_USERS.inc(1)
            task = self.event_loop.create_task(self.echo(connection))
            task.add_done_callback(self.echo_tasks.remove)
            self.echo_tasks.append(task)

    async def close_and_stop(self):
        logger.info("Closing echo tasks...")
        await self.close_echo_tasks()

        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

        logger.info("Server socket closed. Waiting for listener to finish...")

    async def close_echo_tasks(self):
        for task in self.echo_tasks:
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=self.settings.timeout_time)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logger.warning("Timeout while closing echo task")

    async def main(self):
        asyncio.create_task(
            start_metrics_server(self.settings.host, self.settings.port_metrics)
        )
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        logger.info(f"Server metrics /metrics server started on {self.settings.port_metrics}")
        
        server_address = (self.settings.host, self.settings.port)
        self.server_socket.setblocking(False)
        self.server_socket.bind(server_address)
        self.server_socket.listen()

        logger.info(f"Server was running {server_address}. Waiting connections...")
        for signame in ["SIGINT", "SIGTERM"]:
            self.event_loop.add_signal_handler(
                getattr(signal, signame),
                lambda s=signame: self.shutdown(s)
            )
            
        SERVICE_STARTS.inc(1)
        COUNT_ACTIVE_USERS.set(0)
        await self.connection_listener(self.server_socket)

if __name__ == "__main__":
    server_settings = settings.get_server_settings()

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    echo_server = EchoServer(event_loop, server_settings)
    
    try:
        event_loop.run_until_complete(echo_server.main())
    except asyncio.CancelledError:
        pass
    except RuntimeError:
        pass
    finally:
        logger.info("Echo server has terminated")
