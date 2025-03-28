from flask import Blueprint, jsonify
from flask_restx import Namespace, Resource
from utils.db_utils import get_capstone_db_connection

test_bp = Blueprint('test_bp', __name__)

db_ns = Namespace('database', description='Database related operations')

# 데이터베이스 연결 테스트 라우트
@db_ns.route('/db-test')
class DBTestResource(Resource):
    def get(self):
        try:
            conn = get_capstone_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
            conn.close()
            return {"message": "Database connection successful"}, 200
        except Exception as e:
            return {"message": "Database connection failed", "error": str(e)}, 500