"""
할 일 관리 앱 (Streamlit 버전)

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
    text = text.strip()
    if text == "":
        return  # 빈 내용은 추가하지 않음
    if category not in CATEGORIES:
        category = "personal"

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
    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1.2, 1])
        with col1:
            new_text = st.text_input(
                "할 일", placeholder="할 일을 입력하세요", label_visibility="collapsed"
            )
        with col2:
            new_cat = st.selectbox(
                "카테고리",
                options=list(CATEGORIES.keys()),
                format_func=lambda c: CATEGORIES[c][0],
                label_visibility="collapsed",
            )
        with col3:
            submitted = st.form_submit_button("추가", use_container_width=True)
        if submitted:
            add_todo(new_text, new_cat)
            st.rerun()

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

    for todo in visible:
        # --- 수정 모드 ---
        if st.session_state.editing_id == todo["id"]:
            ec1, ec2, ec3, ec4 = st.columns([3, 1.2, 0.8, 0.8])
            with ec1:
                edit_text = st.text_input(
                    "수정", value=todo["text"],
                    key=f"edit_text_{todo['id']}",
                    label_visibility="collapsed",
                )
            with ec2:
                cat_keys = list(CATEGORIES.keys())
                edit_cat = st.selectbox(
                    "카테고리", options=cat_keys,
                    index=cat_keys.index(todo["category"]),
                    format_func=lambda c: CATEGORIES[c][0],
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
