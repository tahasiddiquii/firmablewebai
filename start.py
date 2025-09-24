#!/usr/bin/env python3
"""
Railway startup script for FirmableWebAI
This ensures the app starts correctly on Railway
"""

import os
import sys

def main():
    print("🚂 Railway startup script starting...")
    
    # Environment check
    port = os.environ.get("PORT", "8000")
    print(f"PORT environment variable: {port}")
    
    # Import check
    try:
        print("Importing required modules...")
        import uvicorn
        print("✓ uvicorn imported")
        
        import main
        print("✓ main module imported")
        print(f"✓ FastAPI app: {main.app}")
        print(f"✓ Live mode: {main.LIVE_MODE}")
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Start the server
    print(f"🚀 Starting uvicorn server on 0.0.0.0:{port}")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(port),
            reload=False,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
