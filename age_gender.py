import cv2
import redis
import grpc
import aggregator_pb2
import aggregator_pb2_grpc
import numpy as np
from deepface import DeepFace
from concurrent import futures
import logging
from datetime import datetime

logging.basicConfig(filename='age_gender.log', level=logging.INFO, format='%(asctime)s - %(message)s')
DETECTOR_BACKEND = 'yunet'  # Test different backends here
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class AggregatorServicer(aggregator_pb2_grpc.AggregatorServicer):
    def SaveFaceAttributes(self, request, context):
        try:
            start_time = datetime.now()
            logging.info(f"Starting age/gender estimation for redis_key: {request.redis_key} with backend: {DETECTOR_BACKEND}")

            image = cv2.imdecode(np.frombuffer(request.frame, np.uint8), -1)
            if image is None:
                raise ValueError("Failed to decode image from bytes")
            
            analysis_start = datetime.now()
            result = DeepFace.analyze(
                image,
                actions=['age', 'gender'],
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=False
            )
            logging.info(f"Age/gender analysis completed in {(datetime.now() - analysis_start).total_seconds()} seconds")
            
            if isinstance(result, list):
                ages = [r['age'] for r in result]
                genders = [r['dominant_gender'] for r in result]
                redis_client.hset(request.redis_key, "age", str(ages))
                redis_client.hset(request.redis_key, "gender", str(genders))
            else:
                redis_client.hset(request.redis_key, "age", result[0]['age'])
                redis_client.hset(request.redis_key, "gender", result[0]['dominant_gender'])
            
            if redis_client.hexists(request.redis_key, "landmarks"):
                channel = grpc.insecure_channel('localhost:50053')
                stub = aggregator_pb2_grpc.AggregatorStub(channel)
                stub.SaveFaceAttributes(request)  # Forward original request with image bytes
            
            logging.info(f"Age/gender estimation completed in {(datetime.now() - start_time).total_seconds()} seconds")
            return aggregator_pb2.FaceResultResponse(response=True)
        except Exception as e:
            logging.error(f"Error in Age/Gender Service: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.UNKNOWN)
            return aggregator_pb2.FaceResultResponse(response=False)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
aggregator_pb2_grpc.add_AggregatorServicer_to_server(AggregatorServicer(), server)
server.add_insecure_port('[::]:50052')
print("Age/Gender Service running on port 50052...")
server.start()
server.wait_for_termination()