from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

# Blueprint 임포트
from routes.chat_route import chat_bp
from routes.schedule_route import schedule_bp
from routes.personality_route import personality_bp
from routes.recommend_routes import recommend_routes
from routes.test_route import test_bp, db_ns

# flask_restx 로드
from flask_restx import Api

# .env 로드
load_dotenv()

# swagger-ui 로드
api = Api(version='1.0', title='어르심 API', description='어르심 AI API', doc="/api-docs")

def create_app():
    # Flask 앱 생성
    app = Flask(__name__)

    # CORS 설정
    CORS(app)

    # swagger-ui 설정
    api.init_app(app)

    # Blueprint 등록
    app.register_blueprint(chat_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(personality_bp)
    app.register_blueprint(recommend_routes)
    app.register_blueprint(test_bp)

    # swagger-ui api 매핑
    api.add_namespace(db_ns)

    return app

if __name__ == "__main__":
    app = create_app()
    # 원하는 포트 번호
    app.run(host="0.0.0.0", port=5000, debug=True)
