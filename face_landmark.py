import cv2
import dlib
import redis
import grpc
import aggregator_pb2
import aggregator_pb2_grpc
import numpy as np
from concurrent import futures
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='face_landmark.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Initialize dlib face detector and predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class AggregatorServicer(aggregator_pb2_grpc.AggregatorServicer):
    def SaveFaceAttributes(self, request, context):
        try:
            start_time = datetime.now()
            logging.info(f"Starting face detection for redis_key: {request.redis_key}")

            image = cv2.imdecode(np.frombuffer(request.frame, np.uint8), -1)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            
            if len(faces) > 0:
                landmark_start = datetime.now()
                logging.info(f"Face detected, starting landmark extraction for redis_key: {request.redis_key}")
                
                all_landmarks = []
                for face in faces:
                    shape = predictor(gray, face)
                    landmarks = [(p.x, p.y) for p in shape.parts()]
                    all_landmarks.append(landmarks)
                
                redis_client.hset(request.redis_key, "landmarks", str(all_landmarks))
                logging.info(f"Landmark extraction completed in {(datetime.now() - landmark_start).total_seconds()} seconds")
                
                if redis_client.hexists(request.redis_key, "age"):
                    channel = grpc.insecure_channel('localhost:50053')
                    stub = aggregator_pb2_grpc.AggregatorStub(channel)
                    stub.SaveFaceAttributes(request)
            
            logging.info(f"Face detection completed in {(datetime.now() - start_time).total_seconds()} seconds")
            return aggregator_pb2.FaceResultResponse(response=True)
        except Exception as e:
            logging.error(f"Error in Face Landmark Service: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.UNKNOWN)
            return aggregator_pb2.FaceResultResponse(response=False)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
aggregator_pb2_grpc.add_AggregatorServicer_to_server(AggregatorServicer(), server)
server.add_insecure_port('[::]:50051')
print("Face Landmark Service running on port 50051...")
server.start()
server.wait_for_termination()