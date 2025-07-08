#!/usr/bin/env python3
"""
Helper script to install dependencies and run the Streamlit meal planner app
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("📝 Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False
    
    # Read .env file to check for OpenAI API key
    with open(".env", "r") as f:
        content = f.read()
        if "OPENAI_API_KEY" not in content:
            print("❌ OPENAI_API_KEY not found in .env file!")
            print("📝 Please add your OpenAI API key to the .env file:")
            print("OPENAI_API_KEY=your_api_key_here")
            return False
    
    print("✅ .env file found with OpenAI API key!")
    return True

def run_streamlit():
    """Run the Streamlit application"""
    print("🚀 Starting Streamlit application...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to run application: {e}")

def main():
    print("🍽️ Meal Planner AI Chat Setup")
    print("=" * 40)
    
    # Check environment file
    if not check_env_file():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    print("\n" + "=" * 40)
    print("🎉 Setup complete! Starting the application...")
    print("📱 Open your browser and go to: http://localhost:8501")
    print("⛔ Press Ctrl+C to stop the application")
    print("=" * 40 + "\n")
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main() 