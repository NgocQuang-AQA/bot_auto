"""Application constants and configuration values"""

# Server Configuration
DEFAULT_PORT = 5000
DEFAULT_HOST = 'localhost'
DEFAULT_DEBUG_PORT = 5678

# Project Configuration
SUPPORTED_PROJECTS = ["mlm", "vkyc", "edpadmin", "edpdob"]

# URL Configuration
DEFAULT_BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
HEALTH_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"

# Logging Configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE = "bot_slack.log"
LOGS_DIR = "logs"

# Docker Configuration
DEFAULT_REDIS_PORT = 6379
DEFAULT_WORKER_CONNECTIONS = 1000
DEFAULT_HTTP_SERVER_PORT = 8080

# Test Configuration
TEST_TIMESTAMP = "1234567890.123456"
TEST_SLACK_WEBHOOK = "https://hooks.slack.com/commands/1234/5678"
TEST_MESSAGE_SIZE_LIMIT = 4000
TEST_LARGE_MESSAGE_SIZE = 1000

# Security Configuration
MAX_AGE_HSTS = 31536000  # 1 year in seconds
DEFAULT_USER_ID = 1000

# File Limits
MAX_FILE_DESCRIPTORS = 65536
MAX_PROCESSES = 4096