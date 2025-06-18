#!/usr/bin/env python3
"""
Simple test script to verify refactoring is working correctly
"""

import sys
import os

# Test imports
try:
    # Test constants import
    from constants import SUPPORTED_PROJECTS, DEFAULT_PORT, DEFAULT_HOST
    print("✅ Constants imported successfully")
    print(f"   SUPPORTED_PROJECTS: {SUPPORTED_PROJECTS}")
    print(f"   DEFAULT_PORT: {DEFAULT_PORT}")
    print(f"   DEFAULT_HOST: {DEFAULT_HOST}")
    
    # Test utils.common import
    from utils.common import setup_project_path, setup_logging, validate_project_name
    print("✅ Utils.common imported successfully")
    
    # Test project path setup
    setup_project_path()
    print("✅ Project path setup completed")
    
    # Test logging setup
    logger = setup_logging(__name__)
    logger.info("Test log message")
    print("✅ Logging setup completed")
    
    # Test project validation
    is_valid, msg = validate_project_name("mlm")
    print(f"✅ Project validation test: {is_valid}, {msg}")
    
    is_valid, msg = validate_project_name("invalid_project")
    print(f"✅ Invalid project test: {is_valid}, {msg}")
    
    # Test config import
    from config.settings import Config
    print("✅ Config imported successfully")
    print(f"   SUPPORTED_PROJECTS: {Config.SUPPORTED_PROJECTS}")
    
    print("\n🎉 All refactoring tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)