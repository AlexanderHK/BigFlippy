#!/usr/bin/env python3
"""
Test ZMQ communication between Flask app and FlipDisk backend
"""
import zmq
import json
import time

def test_publisher():
    """Test sending messages like the Flask app would"""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5556")  # Use different port for testing
    
    print("ZMQ Publisher started on port 5556")
    time.sleep(1)  # Allow time for subscriber to connect
    
    # Test messages
    messages = [
        {"command": "standby"},
        {"command": "weather"},
        {"command": "cycle"},
        {"command": "image", "image_path": "/path/to/test.jpg", "folder": "SimpleBW"}
    ]
    
    for msg in messages:
        socket.send_string(json.dumps(msg))
        print(f"Sent: {msg}")
        time.sleep(2)
    
    socket.close()
    context.term()

def test_subscriber():
    """Test receiving messages like FlipDisk would"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    
    print("ZMQ Subscriber started, listening...")
    
    try:
        while True:
            message = socket.recv_string(zmq.NOBLOCK)
            data = json.loads(message)
            print(f"Received: {data}")
    except zmq.Again:
        print("No more messages")
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sub":
        test_subscriber()
    else:
        test_publisher()