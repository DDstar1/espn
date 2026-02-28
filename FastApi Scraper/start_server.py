import os
import sys
import uvicorn

def main():
    host = os.getenv("SERVER_HOST", "localhost")
    port = 8000

    # Optional: read from environment variables
    port = int(os.getenv("PORT", port))

    print(f"Starting server on {host}:{port}")
    print(f"Platform: {sys.platform}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True  # change to True for development only
    )

if __name__ == "__main__":
    main()