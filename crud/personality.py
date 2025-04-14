from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.personality import Personality

def get_latest_personality_by_user_id(db: Session, user_id: int) -> Personality | None:
    result = db.query(Personality).filter(Personality.user_id == user_id).order_by(Personality.id.desc()).first()

    if not result:
        raise HTTPException(status_code=404, detail="유저 정보를 찾을 수 없습니다")

    return result

def create_personality(
    db: Session,
    user_id: int,
    ei: str,
    sn: str,
    tf: str,
    jp: str,
    personality_tags: list[str]
) -> Personality | None:
    personality = Personality(
        user_id=user_id,
        ei=ei,
        sn=sn,
        tf=tf,
        pj=jp,
        tag=",".join(personality_tags)
    )
    db.add(personality)
    db.commit()
    db.refresh(personality)
    return personality