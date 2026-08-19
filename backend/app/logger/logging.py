"""
Application logger configuration.
"""

from loguru import logger
import sys

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

logger.add(
    "logs/application.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
)

app_logger = logger