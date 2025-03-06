import cv2
import grpc
import aggregator_pb2
import aggregator_pb2_grpc
import hashlib
import os
from datetime import datetime

# Folder containing test images
TEST_IMAGES_FOLDER = "test_images"

def process_image(image_path):
    # Load the image and convert to JPEG bytes
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return
    
    _, image_bytes = cv2.imencode(".jpg", image)
    image_hash = hashlib.md5(image_bytes).hexdigest()  # Unique key for Redis
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp

    # Connect to Face Landmark Service (port 50051)
    face_channel = grpc.insecure_channel('localhost:50051')
    face_stub = aggregator_pb2_grpc.AggregatorStub(face_channel)
    face_request = aggregator_pb2.FaceResult(
        time=timestamp,
        frame=image_bytes.tobytes(),
        redis_key=image_hash
    )
    face_response = face_stub.SaveFaceAttributes(face_request)
    print(f"Face Landmark Response for {os.path.basename(image_path)}: {face_response.response}")

    # Connect to Age/Gender Service (port 50052)
    age_channel = grpc.insecure_channel('localhost:50052')
    age_stub = aggregator_pb2_grpc.AggregatorStub(age_channel)
    age_request = aggregator_pb2.FaceResult(
        time=timestamp,
        frame=image_bytes.tobytes(),
        redis_key=image_hash
    )
    age_response = age_stub.SaveFaceAttributes(age_request)
    print(f"Age/Gender Response for {os.path.basename(image_path)}: {age_response.response}")

def main():
    # Ensure the test images folder exists
    if not os.path.exists(TEST_IMAGES_FOLDER):
        print(f"Error: Folder '{TEST_IMAGES_FOLDER}' not found.")
        return
    
    # Get all image files from the folder
    image_files = [f for f in os.listdir(TEST_IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No images found in '{TEST_IMAGES_FOLDER}'.")
        return
    
    print(f"Found {len(image_files)} images to process.")
    
    # Process each image
    for image_file in image_files:
        image_path = os.path.join(TEST_IMAGES_FOLDER, image_file)
        print(f"Processing {image_path}...")
        process_image(image_path)

if __name__ == "__main__":
    main()