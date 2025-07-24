import requests
import json

# Janus server URL
JANUS_URL = f'http://localhost:8088/janus'

def create_session():
    create_payload = {
        "janus": "create",
        "transaction": "unique_transaction_id_11"
    }
    try:
        session_response = requests.post(JANUS_URL, json=create_payload)
        session_response.raise_for_status()
        session_id = session_response.json()['data']['id']
        return session_id
    except requests.exceptions.RequestException as e:
        print(f"Failed to create session: {e}")
        if 'session_response' in locals():
            print(f"Response content: {session_response.content}")
        return None

def attach_plugin(session_id):
    attach_payload = {
        "janus": "attach",
        "plugin": "janus.plugin.streaming",
        "transaction": "unique_transaction_id_12"
    }
    try:
        attach_response = requests.post(f"{JANUS_URL}/{session_id}", json=attach_payload)
        attach_response.raise_for_status()
        handle_id = attach_response.json()['data']['id']
        return handle_id
    except requests.exceptions.RequestException as e:
        print(f"Failed to attach to plugin: {e}")
        if 'attach_response' in locals():
            print(f"Response content: {attach_response.content}")
        return None

def add_stream(session_id, handle_id):
    add_stream_payload = {
        "janus": "message",
        "body": {
            "request": "create",
            "type": "rtsp",
            "id": 99,
            "description": "RTSP Stream",
            "url": "rtsp://rtspstream:09e66422b8eb98a6acd4f993806a48dc@zephyr.rtsp.stream/movie",
            "audio": False,
            "video": True,
            "videofmtp" : "profile-level-id=42e01f;packetization-mode=1",
        },
        "transaction": "unique_transaction_id_13"
    }
    try:
        add_stream_response = requests.post(f"{JANUS_URL}/{session_id}/{handle_id}", json=add_stream_payload)
        add_stream_response.raise_for_status()
        return add_stream_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to add stream: {e}")
        if 'add_stream_response' in locals():
            print(f"Response content: {add_stream_response.content}")
        return None

def main():
    session_id = create_session()
    if not session_id:
        return
    
    handle_id = attach_plugin(session_id)
    if not handle_id:
        return
    
    add_stream_response = add_stream(session_id, handle_id)
    if not add_stream_response:
        return
    
    print(json.dumps(add_stream_response, indent=2))

if __name__ == "__main__":
    main()
