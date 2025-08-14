from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services import attendance_service
from ..utils import image_utils

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)

@router.post("/mark")
async def mark_attendance_endpoint(
    subject: str = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Mark attendance by recognizing faces in an uploaded image.

    - **subject**: The subject for which attendance is being taken (e.g., 'Math').
    - **image_file**: An image containing faces of students.
    """
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    cv2_image = await image_utils.to_cv2_image(image_file)
    
    return attendance_service.mark_attendance(db=db, subject=subject, image=cv2_image)


@router.get("/summary/{subject}")
def get_attendance_summary_endpoint(subject: str, db: Session = Depends(get_db)):
    """
    Get a summary of attendance for a specific subject.
    Calculates the attendance percentage for each registered student.
    """
    summary = attendance_service.get_attendance_summary(db=db, subject=subject)
    if not summary:
        raise HTTPException(status_code=404, detail=f"No student or attendance data found for subject '{subject}'.")
    return summary