from flask import Blueprint, jsonify
from chat_utils import fetch_user_personality, fetch_all_courses, get_course_personality

recommend_routes = Blueprint('recommend_routes', __name__)

@recommend_routes.route("/recommend_all/<user_id>", methods=["GET"])
def recommend_all_programs(user_id):
    personality_data = fetch_user_personality(user_id)
    if not personality_data:
        return jsonify({"error": "사용자 성향 정보를 가져오지 못했습니다."}), 404

    ei_value = personality_data.get("ei", "")
    if ei_value == "E":
        target_personality = "외향형"
    elif ei_value == "I":
        target_personality = "내향형"
    else:
        return jsonify({"error": "알 수 없는 성향 정보입니다."}), 400

    courses = fetch_all_courses()
    if not courses:
        return jsonify({"error": "현재 등록된 프로그램이 없습니다."}), 404

    matched_list = [
        row for row in courses 
        if get_course_personality(row["course"]) == target_personality
    ]

    if not matched_list:
        return jsonify({"message": f"'{target_personality}' 성향에 맞는 프로그램이 없습니다."}), 404

    return jsonify({
        "user_id": user_id,
        "성향": target_personality,
        "matched_programs": matched_list
    })
