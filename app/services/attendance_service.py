import cv2
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date
from fastapi import HTTPException
import numpy as np

from .. import config
from ..models.attendance import Student, AttendanceRecord

def load_recognizer():
    """Loads the trained LBPH recognizer model from file."""
    if not os.path.exists(config.TRAINED_MODEL_PATH):
        raise HTTPException(status_code=500, detail="Model not found. Please train the model first via the /face-recognition/train endpoint.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(config.TRAINED_MODEL_PATH))
    return recognizer

def mark_attendance(db: Session, subject: str, image: np.ndarray):
    """
    Recognizes faces in a given image and marks attendance in the database.
    """
    recognizer = load_recognizer()
    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="No faces detected in the uploaded image.")

    recognized_students = []
    today = date.today()

    for (x, y, w, h) in faces:
        # Predict the face
        enrollment_id_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        # Check if the recognition is confident enough
        if confidence < config.RECOGNITION_CONFIDENCE_THRESHOLD:
            student = db.query(Student).filter(Student.enrollment_id == str(enrollment_id_pred)).first()
            if student:
                # Check if attendance was already marked for this student, subject, and day
                existing_record = db.query(AttendanceRecord).filter(
                    and_(
                        AttendanceRecord.student_id == student.id,
                        AttendanceRecord.subject == subject,
                        func.date(AttendanceRecord.timestamp) == today
                    )
                ).first()

                if not existing_record:
                    attendance_record = AttendanceRecord(student_id=student.id, subject=subject)
                    db.add(attendance_record)
                    recognized_students.append({"enrollment_id": student.enrollment_id, "name": student.name, "status": "Attendance Marked"})
                else:
                    recognized_students.append({"enrollment_id": student.enrollment_id, "name": student.name, "status": "Already Marked Today"})
    
    if not recognized_students:
        raise HTTPException(status_code=404, detail="No known students were recognized in the image.")
        
    db.commit()
    return recognized_students

def get_attendance_summary(db: Session, subject: str):
    """
    Calculates and returns the attendance summary for a given subject.
    """
    students = db.query(Student).all()
    if not students:
        return []

    # Get the total number of unique class days for the subject
    total_days_query = db.query(func.count(func.distinct(func.date(AttendanceRecord.timestamp)))).filter(AttendanceRecord.subject == subject)
    total_class_days = total_days_query.scalar() or 0

    if total_class_days == 0:
        return [{"enrollment_id": s.enrollment_id, "name": s.name, "attendance_percentage": "0%"} for s in students]

    # Get the number of days each student was present
    attendance_counts = db.query(
        AttendanceRecord.student_id,
        func.count(AttendanceRecord.id).label("days_present")
    ).filter(AttendanceRecord.subject == subject).group_by(AttendanceRecord.student_id).all()
    
    present_map = {student_id: count for student_id, count in attendance_counts}
    
    # Calculate percentage for each student
    summary = []
    for student in students:
        days_present = present_map.get(student.id, 0)
        percentage = round((days_present / total_class_days) * 100) if total_class_days > 0 else 0
        summary.append({
            "enrollment_id": student.enrollment_id,
            "name": student.name,
            "days_present": days_present,
            "total_class_days": total_class_days,
            "attendance_percentage": f"{percentage}%"
        })

    return summary