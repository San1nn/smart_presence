from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import connection
from app.database.connection import get_db
from app.models import attendance as models
from app.routes import attendance, face_recognition, auth
# Import the new dependency from auth_service
from app.services.auth_service import try_get_current_user
from app.config import HAAR_CASCADE_PATH

templates = Jinja2Templates(directory="app/templates")
models.Base.metadata.create_all(bind=connection.engine)
app = FastAPI(title="Smart Presence")

# Include Routers
app.include_router(auth.router)
app.include_router(face_recognition.router)
app.include_router(attendance.router)

@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db), user: Optional[models.User] = Depends(try_get_current_user)):
    """
    Serves the main page.
    - If the user is logged in, it shows the 'dashboard.html' page.
    - If the user is not logged in, it shows the public 'landing.html' page.
    """
    if user:
        # User is logged in, show the dashboard
        context = {"request": request, "user": user}
        return templates.TemplateResponse("dashboard.html", context)
    else:
        # User is not logged in, show the public landing page
        return templates.TemplateResponse("landing.html", {"request": request})

# The startup event remains the same
@app.on_event("startup")
async def startup_event():
    if not os.path.exists(HAAR_CASCADE_PATH):
        print("="*80)
        print(f"!! WARNING: Haar Cascade file not found !!")
        print(f"Please download 'haarcascade_frontalface_default.xml' and place it in: {HAAR_CASCADE_PATH.parent}")
        print("="*80)