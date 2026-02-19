"""
Server File: 

This will act as the main server and first entry point for this application. This will just assign a connection handler for each websocket. 
"""

## Lib imports

import os
import asyncio
from functools import partial
from websockets.asyncio.server import serve
from connection_handler import connection_handler
from rate_limiter import RateLimiter, SlidingWindowLimiter

HOST = os.getenv("HOST", "localhost")
PORT = 8765

## Init our rate limiter to apply limits to each client 
client_rate_limiter = RateLimiter(
    SlidingWindowLimiter(max_requests=5, window_seconds=60)
)

async def start_server():
    print("Starting Server...\n(Ctrl+C to exit)")
    handler = partial(connection_handler, limiter=client_rate_limiter)
    async with serve(handler, HOST, PORT, ping_timeout=None) as server:
        await server.serve_forever()

def main():
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nGracefully shutting down server...")

if __name__ == "__main__":
    main()