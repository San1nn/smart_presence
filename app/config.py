from pathlib import Path

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the data directory, which should be outside the 'app' package
# Project layout will be:
# ./data/
# ./smart_presence/app/
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Path to the Haar Cascade file for face detection
HAAR_CASCADE_PATH = DATA_DIR / "haarcascade_frontalface_default.xml"

# Directory to save training images of students
TRAINING_IMAGE_DIR = DATA_DIR / "TrainingImage"
TRAINING_IMAGE_DIR.mkdir(exist_ok=True)

# Directory and path for the trained model file
TRAINED_MODEL_DIR = DATA_DIR / "TrainingImageLabel"
TRAINED_MODEL_DIR.mkdir(exist_ok=True)
TRAINED_MODEL_PATH = TRAINED_MODEL_DIR / "Trainner.yml"

# --- DATABASE CONFIGURATION CHANGE ---

# Comment out or remove the old SQLite URL
# DATABASE_URL = f"sqlite:///{DATA_DIR / 'smart_presence.db'}"

# New MySQL Database URL
# Format: mysql+<driver>://<user>:<password>@<host>:<port>/<db_name>
DATABASE_URL = "mysql+pymysql://root:root12345@localhost:3306/smart_presence"


# Confidence threshold for face recognition.
RECOGNITION_CONFIDENCE_THRESHOLD = 70.0