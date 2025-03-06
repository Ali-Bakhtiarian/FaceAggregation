import cv2
import redis
import json
import grpc
import aggregator_pb2
import aggregator_pb2_grpc
import numpy as np
from concurrent import futures
import ast
import os

# Ensure output folder exists
output_folder = "output_images"
os.makedirs(output_folder, exist_ok=True)

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class AggregatorServicer(aggregator_pb2_grpc.AggregatorServicer):
    def SaveFaceAttributes(self, request, context):
        try:
            # Get data from Redis
            landmarks_str = redis_client.hget(request.redis_key, "landmarks").decode('utf-8')
            age = redis_client.hget(request.redis_key, "age").decode('utf-8')
            gender = redis_client.hget(request.redis_key, "gender").decode('utf-8')
            
            # Parse landmarks (list of lists for multiple faces)
            all_landmarks = ast.literal_eval(landmarks_str)
            
            # Convert bytes to image
            image = cv2.imdecode(np.frombuffer(request.frame, np.uint8), -1)
            
            # Parse age and gender (lists or single values)
            ages = ast.literal_eval(age) if age.startswith('[') else [age]
            genders = ast.literal_eval(gender) if gender.startswith('[') else [gender]
            
            # Draw landmarks, gender, and age for each face
            for i, landmarks in enumerate(all_landmarks):
                # Draw landmarks as green dots
                for (x, y) in landmarks:
                    cv2.circle(image, (x, y), 2, (0, 255, 0), -1)
                
                # Calculate position for text
                if i < len(genders) and i < len(ages):
                    x_min = min(x for x, y in landmarks)
                    y_min = min(y for x, y in landmarks)
                    
                    # Gender above the face (red)
                    gender_text = f"Gender: {genders[i]}"
                    cv2.putText(image, gender_text, (x_min, y_min - 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Age below gender (blue)
                    age_text = f"Age: {ages[i]}"
                    cv2.putText(image, age_text, (x_min, y_min - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Save the image with landmarks, gender, and age
            output_path = os.path.join(output_folder, f"{request.redis_key}_output.jpg")
            cv2.imwrite(output_path, image)
            print(f"Saved image with landmarks, gender, and age to {output_path}")
            
            # Save as JSON (unchanged, meets task requirements)
            data = {
                "time": request.time,
                "landmarks": landmarks_str,
                "age": age,
                "gender": gender
            }
            with open(f"output/{request.redis_key}.json", "w") as f:
                json.dump(data, f)
            
            return aggregator_pb2.FaceResultResponse(response=True)
        except Exception as e:
            print(f"Error in Data Storage Service: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.UNKNOWN)
            return aggregator_pb2.FaceResultResponse(response=False)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
aggregator_pb2_grpc.add_AggregatorServicer_to_server(AggregatorServicer(), server)
server.add_insecure_port('[::]:50053')
print("Data Storage Service running on port 50053...")
server.start()
server.wait_for_termination()