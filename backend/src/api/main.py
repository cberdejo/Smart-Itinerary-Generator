import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    """
    Main function to run the FastAPI application.
    """
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
