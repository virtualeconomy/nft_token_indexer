import sys
from loguru import logger

logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
#logger.add("api.log", backtrace=True, format="{time:MM-DD at HH:mm:ss} | {level} | {message}", rotation="1 week")
