import logging
import socket
import asyncio
from asyncio import AbstractEventLoop
import signal
from typing import List
from schemas import EchoServerSettings
import settings

class EchoServer:
    def __init__(
        self,
        event_loop:AbstractEventLoop, 
        settings: EchoServerSettings
    ):
        self.echo_tasks: List[asyncio.Task] = []
        self.event_loop = event_loop
        self.settings = settings

    async def echo(self, connection: socket.socket):
        try:
            while data:= await self.event_loop.sock_recv(connection, 1024):
                await self.event_loop.sock_sendall(connection, data)
        except Exception as e:
            logging.exception(e)
        finally:
            connection.close()
    
    def shutdown(self):
        raise

    async def connection_listener(self, server_socket: socket.socket):
        while True:
            connection, address = await self.event_loop.sock_accept(server_socket)
            connection.setblocking(False)
            logging.info(f"Get messages from {address}")
            task = asyncio.create_task(self.echo(connection))
            self.echo_tasks.append(task)
    
    async def close_echo_tasks(self):
        waiters = [asyncio.wait_for(echo_task, timeout=self.settings.timeout_time) for echo_task in self.echo_tasks]
        for task in waiters:
            try:
                await task
            except asyncio.exceptions.TimeoutError:
                logging.exception("Timeout")
    
    async def main(self):
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = ('127.0.0.1', self.settings.port)
        server_socket.setblocking(False)        
        server_socket.listen()

        for signame in ["SIGINT", "SIGTERM"]:
            self.event_loop.add_signal_handler(getattr(signal, signame), self.shutdown)
        
        await self.connection_listener(server_socket)

if __name__ == "__main__":
    server_settings = settings.get_server_settings()
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    echo_server = EchoServer(event_loop, server_settings)

    event_loop.run_until_complete(echo_server.main())
