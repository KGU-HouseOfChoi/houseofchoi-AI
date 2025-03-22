import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG_ELDERLY = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_ELDERLY_DB"),
    "charset": os.getenv("DB_CHARSET")
}

DB_CONFIG_PERSONALITY = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_PERSONALITY_DB"),
    "charset": os.getenv("DB_CHARSET")
}

def get_elderly_db_connection():
    """노인교실, 일정 관련 DB (elderly_db)"""
    return pymysql.connect(**DB_CONFIG_ELDERLY)

def get_personality_db_connection():
    """사용자 대화 로그, 성향 관련 DB (personality_db)"""
    return pymysql.connect(**DB_CONFIG_PERSONALITY)
