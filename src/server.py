"""
This will act as the main server and first entry point for this application. This will just assign a connection handler for each websocket.
Basically, each websocket connection will have a "task", and thus all these connections will be able to process requests concurrently. 
"""

## Lib imports

import os
import asyncio
from functools import partial
from websockets.asyncio.server import serve
from connection_handler import connection_handler
from rate_limiter import RateLimiter, SlidingWindowLimiter
import logging

HOST = os.getenv("HOST", "localhost")
PORT = 8765

## Init our rate limiter to apply limits to each client 
client_rate_limiter = RateLimiter(
    SlidingWindowLimiter(max_requests=5, window_seconds=60)
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/server.log')
    ]
)

async def start_server():
    logging.info("Starting Server...\n(Ctrl+C to exit)")
    handler = partial(connection_handler, limiter=client_rate_limiter)
    async with serve(handler, HOST, PORT, ping_timeout=None) as server:
        await server.serve_forever()

def main():
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("\nGracefully shutting down server...")

if __name__ == "__main__":
    main()