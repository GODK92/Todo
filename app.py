"""
할 일 관리 앱 (Streamlit 버전) - 키워드 기반 자동 카테고리 분류 지원

실행 방법:
    pip install -r requirements.txt
    streamlit run app.py

데이터는 todos.json 파일에 저장되어 새로고침/재실행 후에도 유지됩니다.
"""

import json
import os
import uuid
from datetime import datetime

import streamlit as st

# =========================================================
# 설정
# =========================================================
DATA_FILE = "todos.json"

# 카테고리 코드 → (한글 라벨, 색상)
CATEGORIES = {
    "work": ("업무", "#4f6df5"),
    "personal": ("개인", "#f59e4f"),
    "study": ("공부", "#2bb673"),
}

# 자동 분류용 카테고리별 키워드 사전
CATEGORY_KEYWORDS = {
    "work": [
        "회의", "미팅", "보고서", "보고", "메일", "이메일", "업무", "프로젝트",
        "발표", "고객", "클라이언트", "결재", "출장", "거래처", "계약", "마감",
        "기획", "회사", "팀", "납품", "견적", "리뷰", "배포", "이슈",
    ],
    "study": [
        "공부", "시험", "강의", "인강", "숙제", "과제", "학습", "복습", "예습",
        "독서", "책", "알고리즘", "코딩", "영어", "단어", "자격증", "문제",
        "수업", "논문", "정리노트", "토익", "수학", "리서치", "스터디",
    ],
    "personal": [
        "운동", "헬스", "약속", "쇼핑", "장보기", "병원", "청소", "빨래", "요리",
        "가족", "친구", "여행", "취미", "은행", "약", "미용실", "산책", "식사",
        "영화", "휴식", "생일", "선물", "예약",
    ],
}

DEFAULT_CATEGORY = "personal"  # 키워드가 안 맞을 때 기본값


# =========================================================
# 자동 분류
# =========================================================
def classify_category(text):
    """할 일 텍스트의 키워드를 분석해 카테고리를 추정한다.

    각 카테고리별로 텍스트에 포함된 키워드 개수를 세어 가장 많은 쪽을 고른다.
    매칭이 없으면 기본 카테고리(개인)를 반환한다.
    """
    text = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                scores[cat] += 1

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return DEFAULT_CATEGORY
    return best_cat


# =========================================================
# 저장 / 불러오기 (파일 기반 영속성)
# =========================================================
def load_todos():
    """todos.json에서 할 일 목록을 불러온다. 없거나 손상되면 빈 목록."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    """할 일 목록을 todos.json에 저장한다."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
    except OSError as e:
        st.error(f"저장 실패: {e}")


# =========================================================
# 상태 초기화 (session_state)
# =========================================================
def init_state():
    if "todos" not in st.session_state:
        st.session_state.todos = load_todos()
    if "filter" not in st.session_state:
        st.session_state.filter = "all"
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None


# =========================================================
# 기능 함수 (CRUD)
# =========================================================
def add_todo(text, category):
    """category가 'auto'이면 키워드 기반으로 자동 분류한다."""
    text = text.strip()
    if text == "":
        return  # 빈 내용은 추가하지 않음

    if category == "auto":
        category = classify_category(text)
    elif category not in CATEGORIES:
        category = DEFAULT_CATEGORY

    st.session_state.todos.append(
        {
            "id": uuid.uuid4().hex,
            "text": text,
            "category": category,
            "completed": False,
            "createdAt": datetime.now().isoformat(),
        }
    )

    # 필터가 켜져 있어 새 항목이 안 보이면, 보이도록 필터 이동
    if st.session_state.filter != "all" and st.session_state.filter != category:
        st.session_state.filter = category

    save_todos(st.session_state.todos)


def edit_todo(todo_id, new_text, new_category):
    new_text = new_text.strip()
    if new_text == "":
        return

    # 수정 시에도 자동 분류 지원
    if new_category == "auto":
        new_category = classify_category(new_text)

    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["text"] = new_text
            if new_category in CATEGORIES:
                todo["category"] = new_category
            break
    st.session_state.editing_id = None
    save_todos(st.session_state.todos)


def delete_todo(todo_id):
    st.session_state.todos = [
        t for t in st.session_state.todos if t["id"] != todo_id
    ]
    if st.session_state.editing_id == todo_id:
        st.session_state.editing_id = None
    save_todos(st.session_state.todos)


def toggle_todo(todo_id):
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["completed"] = not todo["completed"]
            break
    save_todos(st.session_state.todos)


# =========================================================
# UI
# =========================================================
def render_badge(category):
    label, color = CATEGORIES.get(category, (category, "#888"))
    return (
        f"<span style='background:{color};color:#fff;font-size:12px;"
        f"font-weight:600;padding:3px 10px;border-radius:999px;'>{label}</span>"
    )


def main():
    st.set_page_config(page_title="할 일 관리", page_icon="✅", layout="centered")
    init_state()

    st.title("✅ 할 일 관리")

    todos = st.session_state.todos

    # ---------- 진행률 ----------
    total = len(todos)
    done = sum(1 for t in todos if t["completed"])
    percent = 0 if total == 0 else round(done / total * 100)

    st.progress(percent / 100)
    st.caption(f"{done}/{total} 완료 ({percent}%)")

    st.divider()

    # ---------- 입력 영역 ----------
    # 카테고리 선택지: 자동 + 수동 3종
    add_options = ["auto"] + list(CATEGORIES.keys())
    add_labels = {"auto": "🤖 자동", **{k: v[0] for k, v in CATEGORIES.items()}}

    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1.3, 1])
        with col1:
            new_text = st.text_input(
                "할 일", placeholder="할 일을 입력하세요", label_visibility="collapsed"
            )
        with col2:
            new_cat = st.selectbox(
                "카테고리",
                options=add_options,
                format_func=lambda c: add_labels[c],
                label_visibility="collapsed",
            )
        with col3:
            submitted = st.form_submit_button("추가", use_container_width=True)
        if submitted:
            add_todo(new_text, new_cat)
            st.rerun()

    st.caption("💡 카테고리를 '🤖 자동'으로 두면 입력한 내용의 키워드로 자동 분류돼요.")

    # ---------- 카테고리 필터 ----------
    filter_options = ["all"] + list(CATEGORIES.keys())
    filter_labels = {"all": "전체", **{k: v[0] for k, v in CATEGORIES.items()}}
    st.session_state.filter = st.radio(
        "필터",
        options=filter_options,
        format_func=lambda c: filter_labels[c],
        index=filter_options.index(st.session_state.filter),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.divider()

    # ---------- 목록 ----------
    current_filter = st.session_state.filter
    visible = [
        t for t in todos
        if current_filter == "all" or t["category"] == current_filter
    ]

    if not visible:
        msg = (
            "아직 할 일이 없어요. 위에서 추가해 보세요!"
            if total == 0
            else "이 카테고리에는 할 일이 없어요."
        )
        st.info(msg)
        return

    # 수정 모드 카테고리 선택지: 자동 + 수동 3종
    edit_options = ["auto"] + list(CATEGORIES.keys())

    for todo in visible:
        # --- 수정 모드 ---
        if st.session_state.editing_id == todo["id"]:
            ec1, ec2, ec3, ec4 = st.columns([3, 1.3, 0.8, 0.8])
            with ec1:
                edit_text = st.text_input(
                    "수정", value=todo["text"],
                    key=f"edit_text_{todo['id']}",
                    label_visibility="collapsed",
                )
            with ec2:
                edit_cat = st.selectbox(
                    "카테고리", options=edit_options,
                    index=edit_options.index(todo["category"]),
                    format_func=lambda c: add_labels[c],
                    key=f"edit_cat_{todo['id']}",
                    label_visibility="collapsed",
                )
            with ec3:
                if st.button("저장", key=f"save_{todo['id']}", use_container_width=True):
                    edit_todo(todo["id"], edit_text, edit_cat)
                    st.rerun()
            with ec4:
                if st.button("취소", key=f"cancel_{todo['id']}", use_container_width=True):
                    st.session_state.editing_id = None
                    st.rerun()
            continue

        # --- 일반 모드 ---
        c1, c2, c3, c4 = st.columns([0.5, 3, 0.8, 0.8])
        with c1:
            checked = st.checkbox(
                "완료", value=todo["completed"],
                key=f"chk_{todo['id']}", label_visibility="collapsed",
            )
            if checked != todo["completed"]:
                toggle_todo(todo["id"])
                st.rerun()
        with c2:
            text_html = todo["text"]
            if todo["completed"]:
                text_html = (
                    f"<span style='text-decoration:line-through;color:#8a8f9c;'>"
                    f"{text_html}</span>"
                )
            st.markdown(
                f"{text_html} &nbsp; {render_badge(todo['category'])}",
                unsafe_allow_html=True,
            )
        with c3:
            if st.button("수정", key=f"edit_{todo['id']}", use_container_width=True):
                st.session_state.editing_id = todo["id"]
                st.rerun()
        with c4:
            if st.button("삭제", key=f"del_{todo['id']}", use_container_width=True):
                delete_todo(todo["id"])
                st.rerun()


if __name__ == "__main__":
    main()
