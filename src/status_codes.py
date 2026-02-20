"""
This is purely to let the clients know about the status of the request that they made. 
All these status codes are standard and I wanted to implement them to
be as close to a production level application as possible. 
"""

from enum import Enum

class StatusCode(Enum):
    OK = 200
    BAD_REQUEST = 400
    FORBIDDEN = 403
    RATE_LIMITED = 429
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503