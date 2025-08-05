import uvicorn
from config.settings import settings


def main():
    """
    Main function to run the FastAPI application.
    """

    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
