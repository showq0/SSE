import requests
import json

def listen_to_sse():
    """Simple SSE client using requests"""
    url = 'http://127.0.0.1:5000/events'

    try:
        with requests.get(url, stream=True, timeout=None) as response:
            event_type = None
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')

                    if line.startswith('event:'):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith('data:'):
                        data = line.split(":", 1)[1].strip()
                        try:
                            parsed_data = json.loads(data)
                            print(f"Received {event_type}: {parsed_data}")
                        except json.JSONDecodeError:
                            print(f"Received {event_type}: {data}")
    except KeyboardInterrupt:
        print("\nSSE client stopped")
    except Exception as e:
        print(f"SSE client error: {e}")

if __name__ == "__main__":
    listen_to_sse()

