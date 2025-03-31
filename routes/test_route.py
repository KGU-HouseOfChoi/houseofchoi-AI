from flask import Blueprint, jsonify
from flask_restx import Namespace, Resource, fields
from utils.db_utils import get_capstone_db_connection
from utils.gpt_utils import gpt_call

test_bp = Blueprint('test_bp', __name__)

test_ns = Namespace('test', description='DB 및 챗봇 test API')

# 데이터베이스 연결 테스트 라우트
@test_ns.route('/db-test')
class DBTestResource(Resource):
    @test_ns.doc(
        description="DB 연결 test API",
        responses = {
            200: "DB 연결 성공",
            500: "DB 연결 실패"
        }
    )
    def get(self):
        """
            DB 연결을 확인하는 API입니다.
        """
        try:
            conn = get_capstone_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
            conn.close()
            return {"message": "Database connection successful"}, 200
        except Exception as e:
            return {"message": "Database connection failed", "error": str(e)}, 500



@test_ns.route('/chatbot-test')
class ChatbotTestResource(Resource):
    @test_ns.doc(
        description="GPT 챗봇 test API",
        responses={
            200: "응답 성공",
            500: "GPT 호출 실패"
        }
    )
    def post(self):
        """
        OpenAI GPT 챗봇 테스트 API
        """
        try:
            user_prompt = "안녕하세요 반가워요!"

            system_prompt = "당신은 친절한 AI 비서입니다."
            response_text = gpt_call(system_prompt, user_prompt)

            return {"message": "GPT 응답 성공", "response": response_text}, 200
        except Exception as e:
            return {"message": "GPT 호출 실패", "error": str(e)}, 500