#!/usr/bin/env python3
"""
Simple test to verify the app structure works
"""

import sys
import os

print("Testing FirmableWebAI structure...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("Testing imports...")
    from fastapi import FastAPI
    print("✓ FastAPI imported successfully")
    
    from pydantic import BaseModel
    print("✓ Pydantic imported successfully")
    
    import uvicorn
    print("✓ Uvicorn imported successfully")
    
    # Test the main module
    print("Testing main module...")
    import main
    print("✓ Main module imported successfully")
    
    print(f"✓ App created: {main.app}")
    print(f"✓ Live mode: {main.LIVE_MODE}")
    
    print("\n✅ All tests passed! The app structure is correct.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
