#!/usr/bin/env python3
"""
Bot Slack Service Runner

This script provides different ways to run the Slack bot service:
- Development mode with debug enabled
- Production mode with optimized settings
- Custom configuration options
"""

import os
import sys
import argparse

# Setup project path
from utils.common import setup_project_path, setup_logging
setup_project_path()

from app.main import app
from config.settings import Config
from constants import DEFAULT_PORT
from waitress import serve

logger = setup_logging(__name__)

# Create config instance
config = Config()

def run_development():
    """Run the application in development mode"""
    logger.info("Starting application in development mode...")
    
    try:
        app.run(
            host='0.0.0.0',
            port=DEFAULT_PORT,
            debug=True
        )
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        raise

def run_production():
    """Run the application in production mode using Waitress"""
    logger.info("Starting application in production mode...")
    
    try:
        serve(
            app,
            host='0.0.0.0',
            port=DEFAULT_PORT,
            threads=4
        )
    except Exception as e:
        logger.error(f"Failed to start production server: {e}")
        raise

def run_custom(host, port, debug, workers):
    """Run with custom configuration"""
    logger.info(f"Starting Bot Slack Service with custom config...")
    logger.info(f"   Host: {host}")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Workers: {workers}")
    
    try:
        if workers > 1:
            logger.info(f"Using Waitress with {workers} threads")
            serve(
                app,
                host=host,
                port=port,
                threads=workers
            )
        else:
            app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start custom server: {e}")
        raise

def validate_environment():
    """Validate required environment variables"""
    try:
        config.validate()
        print("✅ Environment validation passed")
        return True
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bot Slack Service Runner')
    parser.add_argument(
        '--mode', 
        choices=['dev', 'prod', 'custom'], 
        default='dev',
        help='Run mode (default: dev)'
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=DEFAULT_PORT,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--workers', 
        type=int, 
        default=4,
        help='Number of worker threads (default: 4)'
    )
    parser.add_argument(
        '--skip-validation', 
        action='store_true',
        help='Skip environment validation'
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Validate environment unless skipped
    if not args.skip_validation:
        if not validate_environment():
            sys.exit(1)
    
    # Run based on mode
    try:
        if args.mode == 'dev':
            run_development()
        elif args.mode == 'prod':
            run_production()
        elif args.mode == 'custom':
            run_custom(args.host, args.port, args.debug, args.workers)
    except KeyboardInterrupt:
        print("\n👋 Bot Slack Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()