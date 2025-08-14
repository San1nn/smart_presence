import cv2
import os
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List

from .. import config
from ..models.attendance import Student  # Updated model import

def add_student_db(db: Session, roll_number: str, name: str):
    """
    Checks if a student with the given roll number exists.
    This function is now simpler as registration is handled by the auth route.
    It's mainly for validating that the student exists before saving images.
    """
    db_student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not db_student:
        raise HTTPException(
            status_code=404, 
            detail=f"Student with roll number {roll_number} not found. Please register the student first."
        )
    if db_student.name.lower() != name.lower():
         raise HTTPException(
            status_code=400, 
            detail=f"Name mismatch. Roll number {roll_number} is registered to '{db_student.name}', not '{name}'."
        )
    return db_student

async def save_face_images(roll_number: str, name: str, images: List[UploadFile]):
    """Saves face images using the student's roll_number for identification."""
    student_dir = config.TRAINING_IMAGE_DIR / f"{roll_number}_{name}"
    os.makedirs(student_dir, exist_ok=True)

    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    sample_num = 0

    for image_file in images:
        contents = await image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = detector.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            continue

        for (x, y, w, h) in faces:
            sample_num += 1
            # The ID used for training is now the student's primary key (integer)
            # The filename uses the human-readable roll_number
            cv2.imwrite(
                str(student_dir / f"{name}_{roll_number}_{sample_num}.jpg"),
                gray[y:y+h, x:x+w],
            )
    
    if sample_num == 0:
        # Clean up empty directory if no faces were found
        # os.rmdir(student_dir) # Be careful with this in async context
        raise HTTPException(status_code=400, detail="No faces could be detected in the uploaded images.")
        
    return {"message": f"{sample_num} face samples saved for {name} ({roll_number}). Ready for training."}


def train_model():
    """Trains the LBPH face recognition model."""
    if not os.path.exists(config.HAAR_CASCADE_PATH):
        raise HTTPException(status_code=500, detail="Haar Cascade file not found.")
        
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    try:
        # Pass the database session to map roll_number back to student.id
        # This requires modifying get_images_and_labels or handling it differently.
        # Let's simplify: We will train using roll_number as the label ID.
        faces, ids = get_images_and_labels(config.TRAINING_IMAGE_DIR)
        if not faces:
             raise HTTPException(status_code=400, detail="No training data found.")
        
        recognizer.train(faces, np.array(ids))
        recognizer.save(str(config.TRAINED_MODEL_PATH))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {e}")

    return {"message": f"Model trained successfully for {len(set(ids))} users."}


def get_images_and_labels(path):
    """Gets images and uses the roll_number from the filename as the label."""
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if not f.startswith('.')]
    faces = []
    ids = []
    
    for image_path in image_paths:
        for file in os.listdir(image_path):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(image_path, file)
                pil_image = Image.open(full_path).convert("L")
                image_np = np.array(pil_image, "uint8")
                
                # Extract roll number from directory name: "123_JohnDoe" -> "123"
                roll_number_str = os.path.basename(image_path).split("_")[0]
                try:
                    # The recognizer requires integer labels
                    ids.append(int(roll_number_str))
                    faces.append(image_np)
                except ValueError:
                    print(f"Warning: Could not parse roll number from {image_path}. Skipping.")
                    continue
    return faces, ids