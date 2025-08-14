from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service
from ..services.auth_service import get_current_user # To protect routes
from ..models.attendance import User # To check user role

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...),
    name: str = Form(...), # Name is for filename convenience
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Protect this endpoint
):
    """
    Upload face images for a PRE-REGISTERED student.
    - **roll_number**: The roll number of the student (must exist in the DB).
    - **name**: Full name of the student (for file naming).
    - **images**: One or more image files of the student's face.
    """
    if current_user.role not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized to register faces.")
        
    if not images:
        raise HTTPException(status_code=400, detail="No image files uploaded.")
    
    # 1. Verify student exists in DB.
    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    
    # 2. Save the images.
    return await face_rec_service.save_face_images(roll_number=roll_number, name=name, images=images)

@router.post("/train")
def train_model_endpoint(current_user: User = Depends(get_current_user)):
    """
    Trigger the face recognition model training process.
    (Protected endpoint)
    """
    if current_user.role not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized to train the model.")
    return face_rec_service.train_model()