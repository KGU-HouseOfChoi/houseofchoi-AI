import os
from flask import Flask
from dotenv import load_dotenv

# Blueprint 임포트
from routes.chat_route import chat_bp
from routes.schedule_route import schedule_bp
from routes.personality_route import personality_bp
from routes.recommend_routes import recommend_routes

# .env 로드
load_dotenv()

def create_app():
    # Flask 앱 생성
    app = Flask(__name__)

    # Blueprint 등록
    app.register_blueprint(chat_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(personality_bp)
    app.register_blueprint(recommend_routes)

    @app.route("/")
    def index():
        return "안녕하세요! 노인 복지 AI 챗봇 API (모듈화) 입니다."

    return app

if __name__ == "__main__":
    app = create_app()
    # 원하는 포트 번호
    app.run(host="0.0.0.0", port=5000, debug=True)
