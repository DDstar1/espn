# start_server.py
import sys
import uvicorn
from db.config import settings  # import your Pydantic Settings object

def main():
    # Use settings from Pydantic
    host = settings.SERVER_HOST   # fallback if SERVER_HOST is not set
    port = int(settings.PORT )                # fallback if PORT is not set

    print(f"Starting server on {host}:{port}")
    print(f"Platform: {sys.platform}")

    uvicorn.run(
        "main:app",  # path to your FastAPI app
        host=host,
        port=port,
        reload=True  # automatically reloads when files change
    )

if __name__ == "__main__":
    main()