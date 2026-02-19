from abc import ABC, abstractmethod
from collections import deque
import time
import asyncio

## I have used this abstract class since during the initial interview, 
## I had mentioned that although sliding window is simple, token bucket is the most widely used algo. 
## I have it implemented as well, so i can possibly use that too but to keep it simple for now
## I have used only the sliding window algorithm. 

class RateLimitingAlgorithm(ABC):
    @abstractmethod
    async def allow(self, client_id: str) -> bool:
        pass


# I am just using a simple queue implementation with timestamps. The time complexity will be O(n). 

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # client_id from each websocket variable(?) -> deque[timestamps]
        self.lock = asyncio.Lock()

    async def allow(self, client_id: str) -> bool:
        now = time.time()

        async with self.lock:
            if client_id not in self.requests:
                self.requests[client_id] = deque()

            q = self.requests[client_id]

            # Removing expired timestamps
            while q and q[0] <= now - self.window_seconds:
                q.popleft()

            if len(q) >= self.max_requests:
                return False

            q.append(now)
            return True


class RateLimiter:
    def __init__(self, limiter):
        self.limiter = limiter

    async def allow(self, client_id: str):
        return await self.limiter.allow(client_id)
