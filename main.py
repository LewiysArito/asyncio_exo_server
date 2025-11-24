import socket
import asyncio
import signal

import settings
from settings import logger
from asyncio import AbstractEventLoop
from typing import List
from schemas import EchoServerSettings

class EchoServer:
    def __init__(self, event_loop: AbstractEventLoop, settings: EchoServerSettings):
        self.echo_tasks: List[asyncio.Task] = []
        self.event_loop = event_loop
        self.settings = settings
        self.listener_task: asyncio.Task | None = None
        self.server_socket: socket.socket | None = None

    async def echo(self, connection: socket.socket):
        try:
            while data := await self.event_loop.sock_recv(connection, 1024):
                await self.event_loop.sock_sendall(connection, data)
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info(f"Connection close {connection}")
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
            task = self.event_loop.create_task(self.echo(connection))
            self.echo_tasks.append(task)

    async def close_and_stop(self):
        logger.info("Closing echo tasks...")
        await self.close_echo_tasks()

        if self.server_socket:
            self.server_socket.close()

        self.event_loop.stop()

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
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
