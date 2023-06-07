import os
from dotenv import load_dotenv
import logging
#
# DEBUG = False
# LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)


load_dotenv(".env")

logging.info('This is an info message')


logging.info(os.getenv("REDIS_HOST"))
REDIS_HOST = os.getenv("REDIS_HOST")
logging.info(REDIS_HOST)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_PORT = os.getenv("REDIS_PORT")

