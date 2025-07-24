import requests
import time

# Constants
URL = 'http://34.60.157.241:9898/peoplecounting/addStreamCounting/'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ2MjAwNzc5LCJpYXQiOjE3NDQ0Nzc0MTMsImp0aSI6IjE3MjI2ZDA4MWRlMTQ1NTlhOGJjNjc0MjNlYmUyYzY5IiwidXNlcl9pZCI6MSwibmFtZSI6ImJsdWVkb3ZlIn0.ETQL-9-6TloyTdP_Bb05_C3XBCRcew998mbS5wsbh2M',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'http://34.60.157.241:9999',
    'Referer': 'http://34.60.157.241:9999/',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}



def main_loop():
    for i in range(15):
        try:
            post_pyload = {
                "title": f"test {i}",
                "place": "1",
                "url": "rtsp://35.222.205.3:8555/live/905",
                "camera_type": "DEFAULT_TYPE",
                "place_name": "test",
                "category_name": "Gates",
                "model_type": "people",
                "cuda_device": "0"
            }
            # Send POST request
            print("Sending POST request...")
            response = requests.post(URL, headers=HEADERS, json=post_pyload, verify=False)
            response.raise_for_status()

            data = response.json()
            stream_id = data.get("id")
            print(f"Received ID: {stream_id}")

            if stream_id is None:
                print("No ID found in response. Skipping PATCH.")
                continue

           

            # Prepare PATCH payload
            patch_payload = {
                "id": stream_id,
                "title": f"test {i}",
                "place": "1",
                "url": "rtsp://35.222.205.3:8555/live/905",
                "place_name": "test",
                "cords": "[0,0,1080,720]",
                "camera_type": "DEFAULT_TYPE",
                "cords_type": "line",
                "model_type": "people",
                "cuda_device": "0"
            }

            # Send PATCH request
            print(f"Sending PATCH for ID: {stream_id}")
            patch_response = requests.patch(URL, headers=HEADERS, json=patch_payload, verify=False)
            patch_response.raise_for_status()
            print(f"PATCH completed for ID: {stream_id}\n")

        except requests.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

     

if __name__ == "__main__":
    main_loop()

