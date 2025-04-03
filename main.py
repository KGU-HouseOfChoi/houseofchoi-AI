from fastapi import FastAPI
from dotenv import load_dotenv

# router module
from routes.test_route import test_router
from routes.schedule_route import schedule_router

# from flask_cors import CORS
# from flask import Flask

# Blueprint 임포트
# from routes.chat_route import chat_ns
# from routes.personality_route import personality_ns
# from routes.recommend_routes import recommend_ns

# flask_restx 로드
# from flask_restx import Api

# .env 로드
load_dotenv()

app = FastAPI(
    title="어르심 AI API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "어르심 AI 기능 관련 API입니다."}

app.include_router(test_router, prefix="/test", tags=["test"])

# # swagger-ui 로드
# api = Api(version='1.0', title='어르심 API', description='어르심 AI API', doc="/api-docs")
#
# def create_app():
#     # Flask 앱 생성
#     app = Flask(__name__)
#
#     # CORS 설정
#     CORS(app)
#
#     # swagger-ui 설정
#     api.init_app(app)
#
#     # swagger-ui api 매핑
#     api.add_namespace(test_ns, path='/test')
#     api.add_namespace(chat_ns, path='/chat')
#     api.add_namespace(personality_ns, path='/personality')
#     api.add_namespace(schedule_ns, path='/schedule')
#     api.add_namespace(recommend_ns, path='/recommend')
#
#     return app
#
# if __name__ == "__main__":
#     app = create_app()
#     # 원하는 포트 번호
#     app.run(host="0.0.0.0", port=5000, debug=True)
