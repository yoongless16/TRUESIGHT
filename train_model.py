import cv2
import numpy as np
from skimage.feature import local_binary_pattern
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Function to extract LBP features from images
def extract_lbp_features(image, img_size=(128, 128)):
    """
    Extract LBP (Local Binary Pattern) features from an image.

    Args:
        image (np.array): Input image.
        img_size (tuple): Resize image to this size before processing.

    Returns:
        np.array: Flattened feature vector.
    """
    resized_image = cv2.resize(image, img_size)
    gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, P=24, R=3, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 27), range=(0, 26))
    return hist / hist.sum()  # Normalize histogram

# Function to process dataset and extract features
def process_dataset(data_dir, img_size=(128, 128)):
    """
    Process dataset of real and fake images to extract features and labels.

    Args:
        data_dir (str): Path to dataset directory (e.g., with 'real' and 'fake' subfolders).
        img_size (tuple): Resize images to this size before processing.

    Returns:
        tuple: Features and labels.
    """
    features, labels = [], []
    for label, sub_dir in enumerate(["real", "fake"]):
        sub_dir_path = os.path.join(data_dir, sub_dir)
        for image_name in os.listdir(sub_dir_path):
            image_path = os.path.join(sub_dir_path, image_name)
            image = cv2.imread(image_path)
            if image is not None:
                features.append(extract_lbp_features(image, img_size))
                labels.append(label)
    return np.array(features), np.array(labels)

if __name__ == "__main__":
    data_dir = "shazl/FYP 2/deepfake-and-real-images"  
    features, labels = process_dataset(data_dir)
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    joblib.dump(model, "deepfake_model.pkl")
