import uvicorn
from app.config.settings import settings


def main():
    """
    Main function to run the FastAPI application.
    """

    uvicorn.run(
        "application:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
