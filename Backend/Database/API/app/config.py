import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    DATABASE = os.getenv(
        "MYSQL_DATABASE",
        "poupe"
    )