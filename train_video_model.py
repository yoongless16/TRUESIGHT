
import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Function to extract frames from videos
def extract_frames_from_videos(data_dir, frame_rate=1, img_size=(128, 128)):
    """
    Extract frames from videos and assign labels.
    
    Args:
        data_dir (str): Path to dataset directory (e.g., with 'real' and 'fake' subfolders).
        frame_rate (int): Number of frames to extract per second.
        img_size (tuple): Resize frames to this size.
    
    Returns:
        tuple: Features and labels.
    """
    features, labels = [], []
    for label, sub_dir in enumerate(["real", "fake"]):
        sub_dir_path = os.path.join(data_dir, sub_dir)
        for video_name in os.listdir(sub_dir_path):
            video_path = os.path.join(sub_dir_path, video_name)
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
            if frames:
                features.append(np.array(frames).mean(axis=0))  # Single vector per video
                labels.append(label)
    return np.array(features), np.array(labels)

if __name__ == "__main__":
    data_dir = "FYP 2/video_dataset"  # Replace with actual dataset path
    features, labels = extract_frames_from_videos(data_dir)
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    joblib.dump(model, "deepfake_video_model.pkl")
