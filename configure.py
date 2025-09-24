#!/usr/bin/env python3
"""
Configuration script for FirmableWebAI
This script helps set up the environment variables needed for the application
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with the necessary configuration"""
    env_content = """# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database Configuration (PostgreSQL with pgvector) - Optional for local testing
# POSTGRES_URL=postgresql://username:password@localhost:5432/firmablewebai

# API Security
API_SECRET_KEY=your_secure_api_secret_key_here

# Redis Configuration (Optional, for rate limiting)
# REDIS_URL=redis://localhost:6379
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Configuration cancelled.")
            return False
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file successfully!")
        print("📝 Please edit .env and add your actual OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_openai_key():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if api_key == "sk-your-openai-api-key-here":
        print("⚠️  OPENAI_API_KEY is set to placeholder value")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  OPENAI_API_KEY doesn't look like a valid OpenAI key")
        return False
    
    print("✅ OPENAI_API_KEY is configured")
    return True

def install_python_dotenv():
    """Install python-dotenv if not available"""
    try:
        import dotenv
        print("✅ python-dotenv is available")
        return True
    except ImportError:
        print("📦 Installing python-dotenv...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
            print("✅ python-dotenv installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install python-dotenv: {e}")
            return False

def load_env_variables():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def main():
    print("🔧 FirmableWebAI Configuration Script")
    print("=" * 40)
    
    # Step 1: Install python-dotenv if needed
    if not install_python_dotenv():
        print("❌ Cannot proceed without python-dotenv")
        return False
    
    # Step 2: Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("📄 Creating .env file...")
        if not create_env_file():
            return False
    else:
        print("✅ .env file already exists")
    
    # Step 3: Load environment variables
    if not load_env_variables():
        return False
    
    # Step 4: Check configuration
    print("\n🔍 Checking configuration...")
    api_key_ok = check_openai_key()
    
    print("\n📋 Configuration Summary:")
    print(f"  - OpenAI API Key: {'✅' if api_key_ok else '❌'}")
    print(f"  - PostgreSQL: {'✅' if os.getenv('POSTGRES_URL') else '⚠️  Optional'}")
    print(f"  - Redis: {'✅' if os.getenv('REDIS_URL') else '⚠️  Optional'}")
    
    if not api_key_ok:
        print("\n🚨 IMPORTANT: You need to configure your OpenAI API key!")
        print("1. Edit the .env file")
        print("2. Replace 'sk-your-openai-api-key-here' with your actual OpenAI API key")
        print("3. Run this script again to verify")
        return False
    
    print("\n✅ Configuration complete! You can now start the application.")
    print("Run: python3 main.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
