"""Common utility functions and decorators"""

import os
import sys
import logging
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from constants import LOGS_DIR, DEFAULT_LOG_FORMAT


def setup_project_path():
    """Setup project path for imports - replaces manual sys.path.append"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def setup_logging(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup standardized logging configuration
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(LOGS_DIR, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(LOGS_DIR, log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper


def handle_exceptions(default_return: Any = None, log_error: bool = True) -> Callable:
    """Decorator to handle exceptions gracefully
    
    Args:
        default_return: Value to return on exception
        log_error: Whether to log the error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator


def validate_project_name(project: str) -> tuple[bool, str]:
    """Validate project name against supported projects
    
    Args:
        project: Project name to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    from constants import SUPPORTED_PROJECTS
    
    if not project:
        return False, "Project name cannot be empty"
    
    project = project.strip().lower()
    
    if project not in SUPPORTED_PROJECTS:
        return False, f"Project '{project}' not supported. Supported: {', '.join(SUPPORTED_PROJECTS)}"
    
    return True, ""


def create_response_dict(success: bool, message: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Create standardized response dictionary
    
    Args:
        success: Operation success status
        message: Response message
        data: Optional additional data
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data:
        response["data"] = data
    
    return response


def safe_get_env(key: str, default: str = "", required: bool = False) -> str:
    """Safely get environment variable with validation
    
    Args:
        key: Environment variable key
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' is missing")
    
    return value