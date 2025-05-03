from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

# router module
from routes.test_route import test_router
from routes.schedule_route import schedule_router
from routes.recommend_routes import recommend_router
from routes.personality_route import personality_router
from routes.chat_route import chat_router

# .env 로드
load_dotenv()

app = FastAPI(
    title="어르심 AI API",
    version="1.0.0",
    description="어르심 서비스 AI 관련 API입니다.",
    root_path="/ai"
)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "https://houseofchoi-fe.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "어르심 AI 기능 관련 API입니다."}

app.include_router(test_router, prefix="/test", tags=["test"])
app.include_router(schedule_router, prefix="/schedule", tags=["schedule"])
app.include_router(recommend_router, prefix="/recommend", tags=["recommend"])
app.include_router(personality_router, prefix="/personality", tags=["personality"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])