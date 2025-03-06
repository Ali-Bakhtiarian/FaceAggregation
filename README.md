# Face Attribute Aggregation System

This project is a distributed system built with Python, gRPC, and Redis to process images, detect faces, extract facial landmarks, estimate age and gender, and generate annotated outputs. It logs processing times and stores results as JSON files and images with visual annotations.

## Project Overview
The system processes images through a pipeline of microservices:
- **Image Input**: Reads images from a folder and kicks off the pipeline.
- **Face Landmark**: Detects faces and extracts 68 facial landmarks using dlib.
- **Age/Gender**: Estimates age and gender using DeepFace with the YuNet backend.
- **Data Storage**: Saves processed data as JSON files and annotated images.

Services communicate via gRPC, and Redis stores intermediate data during processing.

## Project Structure
```
FaceAggregation/
├── protos/
│   └── aggregator.proto              # gRPC service definition
├── output/                          # JSON output folder (auto-created)
├── output_images/                   # Annotated images folder (auto-created)
├── test_images/                     # Input test images folder
│   └── MultipleFaces.jpg            # Sample test image (add your own)
├── image_input.py                   # Processes input images
├── face_landmark.py                 # Detects faces and landmarks
├── age_gender.py                    # Estimates age and gender
├── data_storage.py                  # Saves JSON and annotated images
├── aggregator_pb2.py                # Generated gRPC file
├── aggregator_pb2_grpc.py           # Generated gRPC file
├── shape_predictor_68_face_landmarks.dat  # dlib model file (download required)
├── .gitignore                       # Excludes logs and outputs from Git
└── README.md                        # This file
```

## Requirements
- **Python**: 3.9 or higher
- **Redis**: A running Redis server (e.g., Redis for Windows)
- **Python Packages**:
  ```bash
  grpcio
  grpcio-tools==1.51.1
  protobuf==3.20.3
  redis
  opencv-python
  deepface
  dlib
  ```
- **dlib Model**: Download `shape_predictor_68_face_landmarks.dat` from [dlib.net](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2).

## Setup Instructions
1. **Clone the Project**:
   - Once uploaded to GitHub, clone it with:
     ```bash
     git clone https://github.com/yourusername/FaceAggregation.git
     cd FaceAggregation
     ```
   - Replace `yourusername` with your GitHub username.

2. **Set Up Conda Environment**:
   ```bash
   conda create -n face_aggregator python=3.9
   conda activate face_aggregator
   ```

3. **Install Dependencies**:
   - Create a `requirements.txt` with the packages listed above.
   - Run:
     ```bash
     pip install -r requirements.txt
     ```

4. **Download dlib Model**:
   - Get `shape_predictor_68_face_landmarks.dat.bz2` from [dlib.net](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2).
   - Extract it to `shape_predictor_68_face_landmarks.dat`.
   - Place it in `FaceAggregation/`.

5. **Install Redis**:
   - Download Redis for Windows from [GitHub](https://github.com/microsoftarchive/redis/releases) (e.g., `Redis-x64-5.0.14.1.zip`).
   - Extract to `C:\Redis`.

6. **Add Test Images**:
   - Create `test_images/` if it doesn’t exist.
   - Add images (e.g., `MultipleFaces.jpg`).

## Running the Project
1. **Start Redis**:
   - In a terminal:
     ```bash
     cd C:\Redis
     redis-server.exe
     ```
   - Ensure it’s running (port 6379).

2. **Run Microservices**:
   - Open four terminals in `FaceAggregation/`.
   - Activate the environment in each:
     ```bash
     conda activate face_aggregator
     ```
   - Run each script:
     - **Terminal 1**: `python face_landmark.py`  
       (Shows: `Face Landmark Service running on port 50051...`)
     - **Terminal 2**: `python age_gender.py`  
       (Shows: `Age/Gender Service running on port 50052...`)
     - **Terminal 3**: `python data_storage.py`  
       (Shows: `Data Storage Service running on port 50053...`)
     - **Terminal 4**: `python image_input.py`  
       (Processes images in `test_images/`)

3. **Check Outputs**:
   - **JSON**: In `output/<hash>.json` (landmarks, age, gender, timing).
   - **Images**: In `output_images/<hash>_output.jpg` (landmarks in green, gender in red, age in blue).
   - **Logs**: `face_landmark.log` and `age_gender.log`.
