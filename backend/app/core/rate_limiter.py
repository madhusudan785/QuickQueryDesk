"""Sliding Window Rate Limiter for FastAPI endpoints."""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import HTTPException, status

class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter.
    
    Tracks timestamps of requests per user ID and enforces maximum request limits
    within a specified time window.
    """

    def __init__(self, max_requests: int = 2, window_hours: int = 12):
        self.max_requests = max_requests
        self.window_seconds = window_hours * 3600
        # Storage: user_id -> list of float timestamps
        self._user_timestamps: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, user_id: str):
        """Check if user has exceeded their request limit in the sliding window.
        
        Raises:
            HTTPException 429 if rate limit is exceeded.
        """
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_seconds

        # Filter out timestamps older than the sliding window
        valid_timestamps = [
            ts for ts in self._user_timestamps[user_id]
            if ts > window_start
        ]
        self._user_timestamps[user_id] = valid_timestamps

        if len(valid_timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Ticket creation limit reached. Maximum {self.max_requests} tickets allowed every 12 hours."
            )

        # Record current request timestamp
        self._user_timestamps[user_id].append(now)

# Global rate limiter instance (2 tickets per 12 hours)
ticket_rate_limiter = SlidingWindowRateLimiter(max_requests=2, window_hours=12)
