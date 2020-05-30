from datetime import datetime


def get_timestamp() -> str:
    """Get current datetime in string format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
