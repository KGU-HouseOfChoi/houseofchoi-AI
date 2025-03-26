import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# 각 DB 설정

DB_CONFIG_CAPSTONE = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_NAME"),  # 여기에서 capstone DB 사용
    "charset": os.getenv("DB_CHARSET")
}

# 연결 함수
def get_capstone_db_connection():
    """캡스톤 프로젝트 관련 DB (capstone)"""
    return pymysql.connect(**DB_CONFIG_CAPSTONE)
