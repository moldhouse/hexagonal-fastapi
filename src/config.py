import os
from typing import NamedTuple


class AppConfig(NamedTuple):
    """Configuration on how to run the app"""

    host: str
    port: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables"""
        return cls(host=os.environ["HOST"], port=int(os.environ["PORT"]))

    @classmethod
    def with_free_port(cls) -> "AppConfig":
        """Create a configuration with a free port, useful for testing"""
        return cls(host="0.0.0.0", port=0)
