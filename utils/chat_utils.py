import random
from fastapi.params import Depends
from sqlalchemy.orm import Session

from crud.personality import get_latest_personality_by_user_id
from crud.program import get_program_by_keyword, get_all_programs
from model.program import Program
from utils.database import get_db
from utils.gpt_utils import gpt_call

def fetch_user_personality(user_id):
    """
    DB에서 user_personality 테이블의 최신 성향 데이터를 가져옵니다.
    예: {
      "user_id": 101,
      "ei": "E",
      "sn": "N",
      "tf": "T",
      "jp": "P",
      "personality_tags": "외향적,사회적,활동적"
    }
    """
    pass


def fetch_all_courses():
    """
    elderly_programs 테이블에서 모든 강좌 데이터를 가져옵니다.
    """
    pass


def get_course_personality(course_name):
    """
    (사용 여부에 따라) course_personality 테이블에서
    해당 course_name의 성향(외향형/내향형 등) 조회
    """
    pass


def build_program_message(course_dict: Program):
    """
    elderly_programs 테이블 한 행(course_dict)에 대해,
    사용자에게 안내할 메시지(문자열)를 만들어 반환.
    필요 없거나 더 필요한 필드는 적절히 추가/삭제하세요.
    """
    message = (
        f"✅ 추천 프로그램이 있습니다!\n\n"
        f"프로그램명: {course_dict.name}\n"
        f"기관명: {course_dict.center.name}\n"
        f"주소: {course_dict.center.address}\n"
        f"연락처: {course_dict.center.tel}\n"
        f"요일: {course_dict.fir_day}, {course_dict.sec_day}, "
        f"{course_dict.thr_day}, {course_dict.fou_day}, {course_dict.fiv_day}\n"
        f"시간: {course_dict.start_time} ~ {course_dict.end_time}\n"
        f"금액: {course_dict.price}원\n"
        f"카테고리: {course_dict.main_category} / {course_dict.sub_category}\n"
        f"인원: {course_dict.headcount}\n"
        f"태그: {course_dict.tags}\n"
    )
    return message, course_dict.name


def recommend_random_program(user_id: int, db:Session=Depends(get_db)):
    """
    - user_personality 테이블에서 personality_tags 가져옴
    - elderly_programs 테이블의 tags와 교집합이 2개 이상인 프로그램 중 무작위 추천
    - 없으면 에러 메시지 반환
    - 있으면 build_program_message로 메시지 생성 후 반환
    """
    # 1. 사용자 태그 가져오기
    personality = get_latest_personality_by_user_id(db, user_id)
    user_tags = [tag.strip() for tag in str(personality.tag).split(",") if tag.strip()]

    # 2. 모든 프로그램 정보 가져오기
    programs = get_all_programs(db)

    # 3. 사용자 태그와 비교하여 교집합이 2개 이상이면 추천 후보에 추가
    matched_list = []
    for program in programs:
        program_tag_names = [tag.name for tag in program.tags]
        overlap = set(user_tags) & set(program_tag_names)
        if len(overlap) >= 2:
            matched_list.append(program)

    if not matched_list:
        return "사용자 성향에 맞는 프로그램이 없습니다."

    # 4) 무작위 선택 & 메시지 생성
    chosen = random.choice(matched_list)
    return build_program_message(chosen)


def search_program_in_db(keyword):
    """
    program_name (또는 '프로그램명') 칼럼에
    keyword를 LIKE 연산으로 검색하여 일치하는 레코드 목록 반환
    """
    pass


def search_program_and_build_message(db:Session, program_keyword):
    """
    특정 프로그램명을 검색해서:
    - 찾으면 무작위로 1개 선택 후 build_program_message()
    - 없으면 generate_nonexistent_program_info() 결과 반환
    실제 라우트에서 편하게 쓰기 위해 만든 함수
    """
    results = get_program_by_keyword(db, program_keyword)
    if results:
        chosen = random.choice(results)
        return build_program_message(chosen), chosen.name
    else:
        alt_info = generate_nonexistent_program_info(program_keyword)
        # alt_info는 "현재 센터에는 없지만, 이런 프로그램이 있을 수 있다" 등의 문구
        return alt_info, None


def generate_nonexistent_program_info(keyword):
    """
    GPT를 통해 "DB엔 없지만 사회적으로 존재하는 프로그램" 안내 문구 생성
    """
    system_prompt = """
    당신은 노인 복지 센터에서 프로그램을 추천하는 비서입니다.
    사용자가 특정 프로그램(예: '수영')을 원하지만 DB에는 없을 때,
    '현재 센터에는 없지만, 일반적으로 이런 프로그램이 있을 수 있다'고 안내해 주세요.
    프로그램을 새로 창조하지 말고, 이미 사회에 흔히 존재하는 예시만 들어주세요.
    """
    user_prompt = (
        f"지금 DB에는 '{keyword}' 관련 프로그램이 없어요. "
        f"하지만 일반적으로 이런 프로그램이 있을 수 있다고 설명해 주세요."
    )
    return gpt_call(system_prompt, user_prompt)


def extract_requested_program(user_message):
    """
    GPT를 사용해 사용자 메시지에서 '프로그램명' 추출 (1~2단어).
    없으면 None 반환
    """
    system_prompt = """
    사용자 메시지에서 특정 프로그램명을 정확히 한 단어 또는 두 단어로 추출해 주세요.
    예) '요가 프로그램이 있나요?' -> '요가'
    만약 프로그램명이 명확히 언급되지 않았다면 데이터형 'None'만 반환하세요.
    """
    candidate_program = gpt_call(system_prompt, user_message, max_tokens=20)

    if "none" in candidate_program.lower():
        return None
    return candidate_program.strip()
