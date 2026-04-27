import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True, encoding="utf-8-sig")


def check_connection():
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    conn.close()
    print("Connexion OK!")


if __name__ == "__main__":
    check_connection()
