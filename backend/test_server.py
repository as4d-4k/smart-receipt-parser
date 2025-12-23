import requests

# The URL of your running server
url = 'http://127.0.0.1:5000/api/scan'

# The image we want to send
image_path = 'test.png' 

print(f"Sending {image_path} to server...")

# Open the image in binary mode and send it
with open(image_path, 'rb') as img:
    files = {'file': img}
    response = requests.post(url, files=files)

# Print the reply from the server
print("\n--- SERVER RESPONSE ---")
print(response.json())