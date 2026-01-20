import os
import logging
import boto3
import watchtower
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

AWS_REGION = os.getenv("AWS_REGION")
LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP")
LOG_STREAM = os.getenv("CLOUDWATCH_LOG_STREAM")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not AWS_REGION or not LOG_GROUP or not LOG_STREAM:
    raise RuntimeError("Missing essential environment variables in .env file")

# boto3 client
logs_client = boto3.client("logs", region_name=AWS_REGION)

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group=LOG_GROUP,
    stream_name=LOG_STREAM,
    boto3_client=logs_client,
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[cloudwatch_handler],
)

logger = logging.getLogger("fastapi-logger")
