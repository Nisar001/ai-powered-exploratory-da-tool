"""
Simple server launcher that works around Python 3.14 compatibility issues
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting AI-Powered EDA Platform...")
print("Python version:", sys.version)
print("Working directory:", os.getcwd())

try:
    import uvicorn
    print("✓ uvicorn imported")
    
    print("\n🚀 Starting server on http://0.0.0.0:8000")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nTrying alternative approach...")
    
    # Fallback: Use Python 3.11 if available
    import subprocess
    result = subprocess.run(["py", "-3.11", "--version"], capture_output=True)
    if result.returncode == 0:
        print("Found Python 3.11, restarting with compatible version...")
        subprocess.run(["py", "-3.11", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"])
    else:
        print("\n⚠️  Python 3.14 compatibility issues detected.")
        print("Please use Docker instead:")
        print("  docker-compose up -d")
        sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
