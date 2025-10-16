import os
import sys
from pathlib import Path
import uvicorn

if __name__ == "__main__":
    # Ensure FastAPI app can always be found no matter where this is launched
    sys.path.append(str(Path(__file__).parent))
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="127.0.0.1", port=port)
