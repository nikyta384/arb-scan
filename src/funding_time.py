from datetime import datetime, timezone, timedelta
from logging_config import logger

def same_funding_time_and_soon(markets_data, time_before_funding):
    """
    Checks if both markets have the same fund_time (ms)
    and that it's no later than time_before_funding minutes from now.
    Handles invalid/missing timestamps safely.
    """
    if len(markets_data) != 2:
        return False  # Expect exactly two markets

    # Extract and validate fund_time values
    times = []
    for m in markets_data:
        ts = m.get('fund_time')
        if not isinstance(ts, (int, float)) or ts <= 0:
            return False
        times.append(ts)

    # Check if both timestamps match exactly
    if times[0] != times[1]:
        return False

    try:
        fund_time_utc = datetime.fromtimestamp(times[0] / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return False  # Timestamp out of range or invalid

    now_utc = datetime.now(timezone.utc)
    return now_utc <= fund_time_utc <= now_utc + timedelta(minutes=time_before_funding)
