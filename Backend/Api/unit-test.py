import requests
import urllib.parse
from urllib.parse import urlparse, urlunparse, quote

MEDIAMTX_API_URL = "http://admin:admin@mediamtx-normal-service:9997"  # API port

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
            "sourceOnDemand": True,
        
        }
        
        # Try first API format
        response = requests.post(url, json=body)
        
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
if __name__ == "__main__":
    print("Adding stream to MediaMTX...")
    add_stream_to_mediamtx("11", "rtsp://admin:BlueVision_2030@10.24.28.75:554")