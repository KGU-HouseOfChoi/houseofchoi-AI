from typing import Optional
from sqlalchemy.orm import Session
from model.chat_log import ChatLog

def create_chat_log(db: Session, user_id: str, user_message: str, assistant_response: Optional[str] = None):
    chat_log = ChatLog(
        user_id=int(user_id),
        user_message=user_message,
        assistant_response = assistant_response
    )

    db.add(chat_log)
    db.commit()
    db.refresh(chat_log)
    return chat_log

def create_chat_log_with_program(
        db: Session,
        user_id: str,
        user_message: str,
        assistant_response: Optional[str] = None,
        recommended_program: Optional[str] = None
):
    chat_log = ChatLog(
        user_id=int(user_id),
        user_message=user_message,
        assistant_response = assistant_response,
        recommended_program = recommended_program
    )

    db.add(chat_log)
    db.commit()
    db.refresh(chat_log)
    return chat_log

def get_last_recommended_program_by_user_id(user_id : str, db: Session) -> Optional[str]:
    """
        user_conversation_log에서 user_id와 일치하며
        recommended_program이 NOT NULL인 레코드를
        최신순으로 조회하여 프로그램명을 반환
    """
    last_program = db.query(ChatLog.recommended_program) \
        .filter(ChatLog.user_id == user_id) \
        .filter(ChatLog.recommended_program.isnot(None)) \
        .order_by(ChatLog.id.desc()) \
        .first()

    return last_program if last_program else None