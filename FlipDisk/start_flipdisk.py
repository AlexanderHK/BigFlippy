#!/usr/bin/env python3
"""
FlipDisk System Launcher
Starts both the backend (FlipDisk.py) and frontend (app.py) processes
"""
import subprocess
import sys
import time
import signal
import os
from threading import Thread

class FlipDiskLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True

    def start_backend(self):
        """Start the FlipDisk backend process"""
        try:
            print("🔄 Starting FlipDisk backend...")
            self.backend_process = subprocess.Popen(
                [sys.executable, "Board/FlipDisk.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor backend output in a separate thread
            def monitor_backend():
                for line in iter(self.backend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[BACKEND] {line.strip()}")
                    else:
                        break
            
            Thread(target=monitor_backend, daemon=True).start()
            print("✅ FlipDisk backend started successfully")
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
        return True

    def start_frontend(self):
        """Start the Flask frontend process"""
        try:
            print("🔄 Starting Flask frontend...")
            # Give backend time to initialize ZMQ
            time.sleep(2)
            
            self.frontend_process = subprocess.Popen(
                [sys.executable, "FlaskApp/app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor frontend output in a separate thread
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[FRONTEND] {line.strip()}")
                    else:
                        break
            
            Thread(target=monitor_frontend, daemon=True).start()
            print("✅ Flask frontend started successfully")
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
        return True

    def stop_processes(self):
        """Gracefully stop both processes"""
        print("\n🛑 Shutting down FlipDisk system...")
        self.running = False
        
        if self.frontend_process:
            print("⏹️  Stopping frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                print("✅ Frontend stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing frontend...")
                self.frontend_process.kill()

        if self.backend_process:
            print("⏹️  Stopping backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                print("✅ Backend stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing backend...")
                self.backend_process.kill()

        print("🏁 FlipDisk system shutdown complete")

    def run(self):
        """Main launcher loop"""
        print("🚀 FlipDisk System Launcher")
        print("=" * 40)
        
        # Register signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            self.stop_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start backend first
            if not self.start_backend():
                print("❌ Failed to start backend. Exiting.")
                return 1
            
            # Wait a bit more for backend to fully initialize
            time.sleep(1)
            
            # Start frontend
            if not self.start_frontend():
                print("❌ Failed to start frontend. Stopping backend.")
                self.stop_processes()
                return 1
            
            print("\n🎉 FlipDisk system is running!")
            print("📱 Web interface: http://10.0.0.143:5000")
            print("⌨️  Press Ctrl+C to stop both processes")
            print("=" * 40)
            
            # Keep the launcher running
            try:
                while self.running:
                    # Check if processes are still alive
                    if self.backend_process and self.backend_process.poll() is not None:
                        print("❌ Backend process died unexpectedly")
                        break
                    
                    if self.frontend_process and self.frontend_process.poll() is not None:
                        print("❌ Frontend process died unexpectedly")
                        break
                    
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
        
        finally:
            self.stop_processes()
        
        return 0

def main():
    """Entry point"""
    # Check if required files exist
    required_files = ["Board/FlipDisk.py", "FlaskApp/app.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Please run this launcher from the FlipDisk directory.")
        return 1
    
    launcher = FlipDiskLauncher()
    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())