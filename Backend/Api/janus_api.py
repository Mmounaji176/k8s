
# from Backend.celery_prefork import app as prefork_worker
# @prefork_worker.task
# def main_api(stream_id, webrtc_stream_id, local_stream_url):
#     import requests
#     import json
#     import os
#     from channels.layers import get_channel_layer
#     from asgiref.sync import async_to_sync
#     import django
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
#     django.setup()
#     # Janus server URL
#     IP = "34.60.157.241"
#     JANUS_URL = f'http://{IP}:8088/janus'

#     def create_session():
#         create_payload = {
#             "janus": "create",
#             "transaction": "unique_transaction_id_11"
#         }
#         try:
#             session_response = requests.post(JANUS_URL, json=create_payload)
#             session_response.raise_for_status()
#             session_id = session_response.json()['data']['id']
#             return session_id
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to create session: {e}")
#             if 'session_response' in locals():
#                 print(f"Response content: {session_response.content}")
#             return None

#     def attach_plugin(session_id):
#         attach_payload = {
#             "janus": "attach",
#             "plugin": "janus.plugin.streaming",
#             "transaction": "unique_transaction_id_12"
#         }
#         try:
#             attach_response = requests.post(f"{JANUS_URL}/{session_id}", json=attach_payload)
#             attach_response.raise_for_status()
#             handle_id = attach_response.json()['data']['id']
#             return handle_id
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to attach to plugin: {e}")
#             if 'attach_response' in locals():
#                 print(f"Response content: {attach_response.content}")
#             return None
#     from urllib.parse import quote, urlparse, urlunparse

#     def encode_rtsp_url(url):
#         try:
#             # Parse URL into components
#             parsed = urlparse(url)
            
#             # Split userinfo (if exists)
#             if '@' in parsed.netloc:
#                 userinfo, hostname = parsed.netloc.rsplit('@', 1)
#                 username, password = userinfo.split(':', 1)
                
#                 # Encode username and password separately
#                 encoded_username = quote(username, safe='')
#                 encoded_password = quote(password, safe='')
                
#                 # Reconstruct netloc with encoded credentials
#                 new_netloc = f"{encoded_username}:{encoded_password}@{hostname}"
                
#                 # Reconstruct URL with encoded parts
#                 encoded_url = urlunparse((
#                     parsed.scheme,
#                     new_netloc,
#                     parsed.path,
#                     parsed.params,
#                     parsed.query,
#                     parsed.fragment
#                 ))
#                 print(f"Encoded URL: {encoded_url}")
#                 return encoded_url
#             return url
#         except Exception as e:
#             print(f"Error encoding RTSP URL: {e}")
#             return url
#     def add_stream(session_id, handle_id, stream_id, stream_url):
        
#         new_url = encode_rtsp_url(stream_url)
#         add_stream_payload = {
#         "janus": "message",
#         "body": {
#                 "request": "create",
#                 "type": "rtsp",
#                 "id": stream_id,
#                 "description": "RTSP Stream",
#                 "url": stream_url,
#                 # Use standard ports for better firewall traversal
#                 "videoport": 8004,
#                 "videopt": 96,  # Standard payload type for H.264
                
#                 # Disable audio to reduce complexity
#                 "audio": False,
#                 "video": True,
                
#                 # H.264 configuration for maximum compatibility
#                 "videocodec": "h264",
#                 "videofmtp": (
#                     "profile-level-id=42e01f;"  # Baseline profile, level 3.1
#                     "packetization-mode=1;"     # Single NAL unit mode
#                     "level-asymmetry-allowed=1" # Allow different levels for sender/receiver
#                 ),
#                 "videortpmap": "H264/90000",    # Standard clock rate
                
#                 # Streaming optimization parameters
#                 "min_delay": 0,                 # Minimize initial delay
#                 "max_delay": 500,              # Maximum buffering (ms)
#                 "buffer_size": 2048,           # Reasonable buffer size
                
#                 # Additional options for better compatibility
#                 "rtp_profile": "RTP/SAVPF",    # Required for WebRTC
#             },
#             "transaction": f"stream_{stream_id}"
#         }
#         try:
#             add_stream_response = requests.post(f"{JANUS_URL}/{session_id}/{handle_id}", json=add_stream_payload)
#             add_stream_response.raise_for_status()
            
#             return add_stream_response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to add stream: {e}")
#             async_to_sync(channel_layer.group_send)(
#                 "stat",
#                 {
#                     "type": "ready_state",
#                     "message": "Can't start stream"
#                 }
#             )
#             if 'add_stream_response' in locals():
#                 print(f"Response content: {add_stream_response.content}")
#             return None

#     session_id = create_session()
#     if not session_id:
#         return
    
#     handle_id = attach_plugin(session_id)
#     if not handle_id:
#         return
#     stream_url = f'rtsp://{IP}:8554/live/{stream_id}'
#     new_url = stream_url
#     try:
#         MEDIAMTX_API_URL = f"http://admin:admin@normal_stream:9997/v3/config/paths/add/live/{stream_id}" 
#         body = {         
#             "name": f"test",
#             "source": f"{encode_rtsp_url(local_stream_url)}",
#             "sourceOnDemand": True,
#             # "readUser": "admin",
#             # "readPass": "admin"
#         }
#         mediamtx_response = requests.post(MEDIAMTX_API_URL, json=body)
#         print(mediamtx_response)
       
#         # print(f"----------------MediaMTX response: {mediamtx_response}")
#         new_url = f'rtsp://{IP}:8556/live/{stream_id}'
#     except Exception as e:
#         print(f"------------ Error adding stream to MediaMTX: {e}")
#     add_stream_response = add_stream(session_id, handle_id, stream_id, stream_url)
    
#     print(json.dumps(add_stream_response, indent=2))
   
#     add_stream_response = add_stream(session_id, handle_id,webrtc_stream_id,new_url)
    
#     channel_layer = get_channel_layer('status')
#     async_to_sync(channel_layer.group_send)(
#         "stat",
#         {
#             "type": "ready_state",
#             "message": "Stream is ready"
#         }
#     )
#     print(json.dumps(add_stream_response, indent=2))


# def main_api_delete(stream_id):
#     import requests
#     import json
#     import os
#     # Janus server URL
#     IP = "34.60.157.241"
#     JANUS_URL = f'http://{IP}:8088/janus'

#     def create_session():
#         create_payload = {
#             "janus": "create",
#             "transaction": "unique_transaction_id_11"
#         }
#         try:
#             session_response = requests.post(JANUS_URL, json=create_payload)
#             session_response.raise_for_status()
#             session_id = session_response.json()['data']['id']
#             return session_id
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to create session: {e}")
#             if 'session_response' in locals():
#                 print(f"Response content: {session_response.content}")
#             return None

#     def attach_plugin(session_id):
#         attach_payload = {
#             "janus": "attach",
#             "plugin": "janus.plugin.streaming",
#             "transaction": "unique_transaction_id_12"
#         }
#         try:
#             attach_response = requests.post(f"{JANUS_URL}/{session_id}", json=attach_payload)
#             attach_response.raise_for_status()
#             handle_id = attach_response.json()['data']['id']
#             return handle_id
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to attach to plugin: {e}")
#             if 'attach_response' in locals():
#                 print(f"Response content: {attach_response.content}")
#             return None

#     def delete_stream(session_id, handle_id, stream_id):

#         delete_stream_payload = {
#             "janus": "message",
#             "body": {
#                 "request": "destroy",
#                 "id": stream_id,
#             },
#             "transaction": "unique_transaction_id_13"
#         }
#         try:
#             delete_stream_response = requests.post(f"{JANUS_URL}/{session_id}/{handle_id}", json=delete_stream_payload)
#             delete_stream_response.raise_for_status()
#             return delete_stream_response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to add stream: {e}")
#             if 'add_stream_response' in locals():
#                 print(f"Response content: {add_stream_response.content}")
#             return None

#     session_id = create_session()
#     if not session_id:
#         return
    
#     handle_id = attach_plugin(session_id)
#     if not handle_id:
#         return
    
#     delete_stream_response = delete_stream(session_id, handle_id,stream_id)
#     if not delete_stream_response:
#         return
    
#     print(json.dumps(delete_stream_response, indent=2))


# Fixed Backend/Api/janus_api.py for Kubernetes


# Updated Backend/Api/janus_api.py to match service configuration

from Backend.celery_prefork import app as prefork_worker
import os
import requests
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import django
from urllib.parse import quote, urlparse, urlunparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

@prefork_worker.task
def main_api(stream_id, webrtc_stream_id, local_stream_url):
    """
    Create a stream in Janus using Kubernetes services
    """
    # FIXED: Use correct Kubernetes service names and ports
    JANUS_SERVICE_URL = 'http://janus-service:8088/janus'
    MEDIAMTX_SERVICE_URL = 'http://mediamtx-normal-service:8554'  # RTSP port
    MEDIAMTX_API_URL = 'http://admin:admin@mediamtx-normal-service:9997'     # API port

    
    # External access configuration
    # EXTERNAL_HOST = os.getenv('EXTERNAL_HOST', 'facerec.local')
    # EXTERNAL_RTSP_PORT = os.getenv('EXTERNAL_RTSP_PORT', '30554')
    EXTERNAL_HOST = "mediamtx-normal-service"
    EXTERNAL_RTSP_PORT = "8554"
    def create_session():
        create_payload = {
            "janus": "create",
            "transaction": f"create_session_{stream_id}"
        }
        try:
            session_response = requests.post(JANUS_SERVICE_URL, json=create_payload, timeout=10)
            session_response.raise_for_status()
            session_id = session_response.json()['data']['id']
            print(f"✅ Created Janus session: {session_id}")
            return session_id
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create Janus session: {e}")
            return None

    def attach_plugin(session_id):
        attach_payload = {
            "janus": "attach",
            "plugin": "janus.plugin.streaming",
            "transaction": f"attach_{stream_id}"
        }
        try:
            attach_response = requests.post(f"{JANUS_SERVICE_URL}/{session_id}", json=attach_payload, timeout=10)
            attach_response.raise_for_status()
            handle_id = attach_response.json()['data']['id']
            print(f"✅ Attached to streaming plugin: {handle_id}")
            return handle_id
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to attach to Janus plugin: {e}")
            return None

    def encode_rtsp_url(url):
        try:
            parsed = urlparse(url)
            if '@' in parsed.netloc:
                userinfo, hostname = parsed.netloc.rsplit('@', 1)
                username, password = userinfo.split(':', 1)
                encoded_username = quote(username, safe='')
                encoded_password = quote(password, safe='')
                new_netloc = f"{encoded_username}:{encoded_password}@{hostname}"
                encoded_url = urlunparse((
                    parsed.scheme, new_netloc, parsed.path,
                    parsed.params, parsed.query, parsed.fragment
                ))
                return encoded_url
            return url
        except Exception as e:
            print(f"Error encoding RTSP URL: {e}")
            return url

    def add_stream_to_mediamtx(stream_id, source_url):
        """Add stream to MediaMTX for transcoding"""
        try:
            # FIXED: Use correct MediaMTX API URL and path structure
            url = f"{MEDIAMTX_API_URL}/v3/config/paths/add/live/{stream_id}"
            
            # Alternative API call format (try both)
            alternative_url = f"{MEDIAMTX_API_URL}/v3/config/paths/live/{stream_id}"
            
            body = {
                "name": f"live/{stream_id}",
                "source": encode_rtsp_url(source_url),
                "sourceOnDemand": False,
         
            }
            
            # Try first API format
            response = requests.post(url, json=body, timeout=15)
            
            if response.status_code not in [200, 201]:
                # Try alternative format
                print(f"First API call failed, trying alternative: {alternative_url}")
                response = requests.patch(alternative_url, json=body, timeout=15)
            
            if response.status_code in [200, 201]:
                print(f"✅ Added stream {stream_id} to MediaMTX")
                print(f"MediaMTX response: {response.text}")
                return True
            else:
                print(f"⚠️  MediaMTX API returned: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"❌ Error adding stream to MediaMTX: {e}")
            return False

    def add_stream_to_janus(session_id, handle_id, stream_id, stream_url):
        """Add stream to Janus streaming plugin"""
        add_stream_payload = {
            "janus": "message",
            "body": {
                "request": "create",
                "type": "rtsp",
                "id": stream_id,
                "description": f"Stream {stream_id}",
                "url": stream_url,
                
                # Optimized settings for WebRTC
                "video": True,
                "audio": False,
                "videocodec": "h264",
                "videofmtp": (
                    "profile-level-id=42e01f;"
                    "packetization-mode=1;"
                    "level-asymmetry-allowed=1"
                ),
                "videortpmap": "H264/90000",
                
                # Performance settings
                "min_delay": 0,
                "max_delay": 500,
                "buffer_size": 2048,
                "rtp_profile": "RTP/SAVPF",
            },
            "transaction": f"add_stream_{stream_id}"
        }
        
        try:
            response = requests.post(
                f"{JANUS_SERVICE_URL}/{session_id}/{handle_id}", 
                json=add_stream_payload, 
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('janus') == 'success':
                print(f"✅ Successfully added stream {stream_id} to Janus")
                return result
            else:
                print(f"❌ Janus returned error for stream {stream_id}: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to add stream {stream_id} to Janus: {e}")
            
            # Send error notification
            try:
                channel_layer = get_channel_layer('status')
                async_to_sync(channel_layer.group_send)(
                    "stat",
                    {
                        "type": "ready_state",
                        "message": "Can't start stream"
                    }
                )
            except:
                pass
            return None

    # Main execution flow
    print(f"🚀 Starting stream creation for ID: {stream_id}")
    print(f"📡 Source URL: {local_stream_url}")
    
    # Step 1: Create Janus session
    session_id = create_session()
    if not session_id:
        print("❌ Failed to create Janus session, aborting")
        return False
    
    # Step 2: Attach to streaming plugin
    handle_id = attach_plugin(session_id)
    if not handle_id:
        print("❌ Failed to attach to Janus plugin, aborting")
        return False
    
    # Step 3: Add stream to MediaMTX for transcoding
    print(f"📺 Adding stream {stream_id} to MediaMTX...")
    mediamtx_success = add_stream_to_mediamtx(stream_id, local_stream_url)
    internal_stream_url = None
    webrtc_stream = None
    # Step 4: Create stream URLs
    if mediamtx_success:
        import time
        time.sleep(5)  # Wait for MediaMTX to process the stream
        # Use MediaMTX transcoded stream (internal service-to-service)
        internal_stream_url = f"rtsp://mediamtx-normal-service:8554/live/{stream_id}"
        # External URL for client access
        print(f"✅ Using MediaMTX transcoded stream")
    else:
        # Fallback to direct stream
        internal_stream_url = local_stream_url
        print(f"⚠️  Using direct stream (MediaMTX failed)")
    
    print(f"📺 Internal stream URL: {internal_stream_url}")
    
    # Step 5: Add primary stream to Janus
    print(f"🎬 Adding stream {stream_id} to Janus...")
    webrtc_stream = f"rtsp://mediamtx-primary-service:8554/live/{stream_id}"
    primary_result = add_stream_to_janus(session_id, handle_id, stream_id, webrtc_stream)
    
    # Step 6: Add WebRTC stream to Janus (if different from primary)
    webrtc_result = None
    if webrtc_stream_id != stream_id:
        print(f"🎬 Adding WebRTC stream {webrtc_stream_id} to Janus...")
        webrtc_result = add_stream_to_janus(session_id, handle_id, webrtc_stream_id, internal_stream_url)
    
    # Step 7: Send success notification
    if primary_result:
        try:
            channel_layer = get_channel_layer('status')
            async_to_sync(channel_layer.group_send)(
                "stat",
                {
                    "type": "ready_state",
                    "message": "Stream is ready"
                }
            )
        except Exception as e:
            print(f"Warning: Could not send WebSocket notification: {e}")
        
        print(f"✅ Stream {stream_id} successfully created and ready!")
        
        # Print results for debugging
        if primary_result:
            print("Primary stream result:")
            print(json.dumps(primary_result, indent=2))
        
        if webrtc_result:
            print("WebRTC stream result:")
            print(json.dumps(webrtc_result, indent=2))
        
        return True
    else:
        print(f"❌ Failed to create stream {stream_id}")
        return False


def main_api_delete(stream_id):
    """
    Delete a stream from Janus and MediaMTX using Kubernetes services
    """
    JANUS_SERVICE_URL = 'http://janus-service:8088/janus'
    MEDIAMTX_API_URL = 'http://admin:admin@mediamtx-normal-service:9997'

    def create_session():
        create_payload = {
            "janus": "create",
            "transaction": f"delete_session_{stream_id}"
        }
        try:
            session_response = requests.post(JANUS_SERVICE_URL, json=create_payload, timeout=10)
            session_response.raise_for_status()
            session_id = session_response.json()['data']['id']
            return session_id
        except requests.exceptions.RequestException as e:
            print(f"Failed to create session for deletion: {e}")
            return None

    def attach_plugin(session_id):
        attach_payload = {
            "janus": "attach",
            "plugin": "janus.plugin.streaming",
            "transaction": f"delete_attach_{stream_id}"
        }
        try:
            attach_response = requests.post(f"{JANUS_SERVICE_URL}/{session_id}", json=attach_payload, timeout=10)
            attach_response.raise_for_status()
            handle_id = attach_response.json()['data']['id']
            return handle_id
        except requests.exceptions.RequestException as e:
            print(f"Failed to attach plugin for deletion: {e}")
            return None

    def delete_stream_from_janus(session_id, handle_id, stream_id):
        delete_stream_payload = {
            "janus": "message",
            "body": {
                "request": "destroy",
                "id": stream_id,
            },
            "transaction": f"delete_{stream_id}"
        }
        try:
            delete_response = requests.post(
                f"{JANUS_SERVICE_URL}/{session_id}/{handle_id}", 
                json=delete_stream_payload, 
                timeout=10
            )
            delete_response.raise_for_status()
            result = delete_response.json()
            print(f"✅ Deleted stream {stream_id} from Janus")
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to delete stream {stream_id}: {e}")
            return None

    def delete_stream_from_mediamtx(stream_id):
        """Delete stream from MediaMTX"""
        try:
            url = f"{MEDIAMTX_API_URL}/v3/config/paths/delete/live/{stream_id}"
            response = requests.delete(url, timeout=10)
            
            if response.status_code in [200, 204, 404]:  # 404 is OK - already deleted
                print(f"✅ Deleted stream {stream_id} from MediaMTX")
                return True
            else:
                print(f"⚠️  MediaMTX delete returned: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not delete stream from MediaMTX: {e}")
            return False

    # Main deletion flow
    print(f"🗑️  Deleting stream {stream_id}")
    
    session_id = create_session()
    if not session_id:
        return False
    
    handle_id = attach_plugin(session_id)
    if not handle_id:
        return False
    
    # Delete from Janus
    janus_result = delete_stream_from_janus(session_id, handle_id, stream_id)
    
    # Delete from MediaMTX
    mediamtx_result = delete_stream_from_mediamtx(stream_id)
    
    if janus_result:
        print("Deletion result:")
        print(json.dumps(janus_result, indent=2))
        return True
    
    return False