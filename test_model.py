
import os
import cv2
import numpy as np
import joblib

# Function to extract frames from a video file
def extract_frames_from_video(video_path, frame_rate=1, img_size=(128, 128)):
    """
    Extract frames from a single video for testing.
    
    Args:
        video_path (str): Path to the video file.
        frame_rate (int): Number of frames to extract per second.
        img_size (tuple): Resize frames to this size.
    
    Returns:
        np.array: Flattened feature array for RandomForestClassifier.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    success, frame = cap.read()
    frame_count = 0
    while success:
        if frame_count % int(cap.get(cv2.CAP_PROP_FPS) / frame_rate) == 0:
            resized_frame = cv2.resize(frame, img_size)
            frames.append(resized_frame.flatten())
        success, frame = cap.read()
        frame_count += 1
    cap.release()
    return np.array(frames).mean(axis=0).reshape(1, -1)  # Single feature vector per video

if __name__ == "__main__":
    video_path = "shazl/FYP 2/video_dataset"  # Replace with actual path
    model_path = "deepfake_video_model.pkl"  # Replace with actual model path
    video_features = extract_frames_from_video(video_path)
    video_model = joblib.load(model_path)
    prediction = video_model.predict(video_features)
    print("Prediction:", "Real" if prediction[0] == 1 else "Fake")
