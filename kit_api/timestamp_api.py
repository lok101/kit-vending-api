import time


class TimestampAPI:
    async def async_get_now(self) -> int:
        return int(time.time_ns())
