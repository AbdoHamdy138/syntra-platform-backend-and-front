import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting SYNTRA FastAPI Backend on http://0.0.0.0:{settings.PORT} ...")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)

