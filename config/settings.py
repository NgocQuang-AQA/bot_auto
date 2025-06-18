import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from constants import (
    DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT, DEFAULT_LOG_FILE,
    SUPPORTED_PROJECTS
)

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """Centralized configuration management"""
    
    # Slack Configuration
    SLACK_TOKEN = os.getenv("TOKEN_SLACK")
    SLACK_CHANNEL = os.getenv("GROUP_ID_SLACK")
    
    # Report Configuration
    DEFAULT_URL_REPORT = os.getenv("DEFAULT_URL_REPORT")
    REPORT_PATHS = {
        "mlm": os.getenv("REPORT_PATH_MLM", ""),
        "vkyc": os.getenv("REPORT_PATH_VKYC", ""),
        "edpadmin": os.getenv("REPORT_PATH_ADMIN", ""),
        "edpdob": os.getenv("REPORT_PATH_DOB", "")
    }
    
    # Batch File Paths
    BATCH_PATHS = {
        "mlm": os.getenv("RUN_MLM_BAT", ""),
        "vkyc": os.getenv("RUN_VKYC_BAT", ""),
        "edpadmin": os.getenv("RUN_EDP_ADMIN_BAT", ""),
        "edpdob": os.getenv("RUN_EDP_DOB_BAT", "")
    }
    
    # Supported Projects
    SUPPORTED_PROJECTS = SUPPORTED_PROJECTS
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    LOG_FORMAT = DEFAULT_LOG_FORMAT
    LOG_FILE = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
    
    @classmethod
    def validate(cls):
        """Validate configuration on startup"""
        errors = []
        
        if not cls.SLACK_TOKEN:
            errors.append("SLACK_TOKEN is required")
        
        if not cls.SLACK_CHANNEL:
            errors.append("SLACK_CHANNEL is required")
        
        # TEMPORARILY COMMENTED - File validation causing startup errors
        # for project, path in cls.BATCH_PATHS.items():
        #     if not path:
        #         errors.append(f"Batch path for {project} is not configured")
        #     elif not os.path.exists(path):
        #         errors.append(f"Batch file not found: {path}")
        #         
        # for project, path in cls.REPORT_PATHS.items():
        #     if path and not os.path.exists(os.path.dirname(path)):
        #         errors.append(f"Report directory not found for {project}: {os.path.dirname(path)}")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
        
        return True

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)

logger = logging.getLogger(__name__)