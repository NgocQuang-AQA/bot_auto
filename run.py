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
import logging
from app.main import app
from config.settings import Config

# Create config instance
config = Config()

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_development():
    """Run in development mode"""
    print("🚀 Starting Bot Slack Service in DEVELOPMENT mode...")
    setup_logging(logging.DEBUG)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )

def run_production():
    """Run in production mode"""
    print("🚀 Starting Bot Slack Service in PRODUCTION mode...")
    setup_logging(logging.INFO)
    
    # Use a production WSGI server
    try:
        from waitress import serve
        print("Using Waitress WSGI server")
        serve(
            app,
            host='0.0.0.0',
            port=5000,
            threads=4,
            connection_limit=100,
            cleanup_interval=30,
            channel_timeout=120
        )
    except ImportError:
        print("Waitress not available, falling back to Flask dev server")
        print("⚠️  WARNING: Using Flask dev server in production is not recommended!")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )

def run_custom(host, port, debug, workers):
    """Run with custom configuration"""
    print(f"🚀 Starting Bot Slack Service on {host}:{port}...")
    setup_logging(logging.DEBUG if debug else logging.INFO)
    
    if debug:
        app.run(
            host=host,
            port=port,
            debug=True,
            threaded=True
        )
    else:
        try:
            from waitress import serve
            serve(
                app,
                host=host,
                port=port,
                threads=workers
            )
        except ImportError:
            app.run(
                host=host,
                port=port,
                debug=False,
                threaded=True
            )

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
        default=5000,
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