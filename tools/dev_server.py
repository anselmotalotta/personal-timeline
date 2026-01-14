#!/usr/bin/env python3
"""
Fast Development Server - No Docker Required
Runs components locally for rapid testing and development
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_env():
    """Setup development environment"""
    if Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    else:
        print("⚠️  No .env file found")

def run_ai_services():
    """Run AI services locally on port 8087"""
    print("🚀 Starting AI Services on http://localhost:8087")
    print("📊 Status: http://localhost:8087/status")
    print("🏥 Health: http://localhost:8087/health")
    print("📈 Metrics: http://localhost:8087/metrics")
    print("\n🔄 Hot reload enabled - edit files and see changes instantly!")
    print("🛑 Press Ctrl+C to stop\n")
    
    from ai_services.api import app
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8087, 
        log_level="info"
    )

def run_data_processor():
    """Run data processing tests"""
    print("🔄 Testing Data Processor...")
    
    from data_processing.local_processor import LocalDataProcessor
    processor = LocalDataProcessor()
    
    print(f"✅ Data path: {processor.data_path}")
    # Add more data processing tests here

def run_frontend_proxy():
    """Run a simple proxy to test frontend connectivity"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import requests
    
    app = FastAPI(title="Frontend Test Proxy")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/test-ai-connection")
    async def test_ai_connection():
        """Test if AI services are reachable"""
        try:
            response = requests.get("http://localhost:8087/status", timeout=5)
            return {
                "status": "success",
                "ai_services_reachable": True,
                "ai_status": response.json()
            }
        except Exception as e:
            return {
                "status": "error",
                "ai_services_reachable": False,
                "error": str(e)
            }
    
    print("🌐 Frontend Test Proxy on http://localhost:8088")
    print("🔗 Test AI connection: http://localhost:8088/test-ai-connection")
    
    uvicorn.run(app, host="0.0.0.0", port=8088, log_level="info")

if __name__ == "__main__":
    setup_env()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "ai":
            run_ai_services()
        elif command == "data":
            run_data_processor()
        elif command == "proxy":
            run_frontend_proxy()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("🛠️  Fast Development Server")
        print("=" * 40)
        print("Commands:")
        print("  python dev_server.py ai     - Run AI services (port 8087)")
        print("  python dev_server.py data   - Test data processing")
        print("  python dev_server.py proxy  - Run frontend test proxy (port 8088)")
        print("\n💡 Use these for rapid development without Docker rebuilds!")