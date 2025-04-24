import requests
import json

def shut_down_server():
    try:
        response = requests.post("http://127.0.0.1:8080/shutdown", timeout=10)
        if response.status_code == 200:
            print("FastAPI server is shutting down...")
        else:
            print(f"Failed to shut down FastAPI. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error shutting down FastAPI: {str(e)}")