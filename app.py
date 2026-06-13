import streamlit as st
import anthropic
import re

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="수학 숙제 도우미",
    page_icon="🧮",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=JetBrains+Mono&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

  /* 배경 */
  .stApp { background: #0f1117; color: #e8eaf0; }

  /* 헤더 */
  .hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
  }
  .hero h1 {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7c6af7 0%, #5eead4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: .3rem;
  }
  .hero p { color: #9ca3af; font-size: 1rem; margin: 0; }

  /* 카드 */
  .card {
    background: #1a1d27;
    border: 1px solid #2a2d3d;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
  }

  /* 모드 뱃지 */
  .badge {
    display: inline-block;
    padding: .2rem .75rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 600;
    margin-right: .4rem;
  }
  .badge-solve  { background: #312e81; color: #a5b4fc; }
  .badge-hint   { background: #064e3b; color: #6ee7b7; }
  .badge-explain{ background: #78350f; color: #fcd34d; }
  .badge-check  { background: #1e1b4b; color: #c4b5fd; }

  /* 결과 박스 */
  .result-box {
    background: #111827;
    border-left: 3px solid #7c6af7;
    border-radius: 0 10px 10px 0;
    padding: 1.2rem 1.4rem;
    font-size: .97rem;
    line-height: 1.8;
    white-space: pre-wrap;
  }

  /* 버튼 오버라이드 */
  .stButton > button {
    background: linear-gradient(135deg, #7c6af7, #5eead4) !important;
    color: #0f1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: .55rem 1.8rem !important;
    font-size: 1rem !important;
    transition: opacity .2s !important;
  }
  .stButton > button:hover { opacity: .85 !important; }

  /* textarea / selectbox */
  .stTextArea textarea, .stSelectbox select {
    background: #1a1d27 !important;
    border: 1px solid #2a2d3d !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
  }
  .stSelectbox [data-baseweb="select"] > div {
    background: #1a1d27 !important;
    border: 1px solid #2a2d3d !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
  }

  /* 구분선 */
  hr { border-color: #2a2d3d !important; }

  /* 예시 버튼 그리드 */
  .example-grid { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .5rem; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🧮 수학 숙제 도우미</h1>
  <p>문제를 입력하면 풀이·힌트·개념 설명까지 도와드려요</p>
</div>
""", unsafe_allow_html=True)

# ── 사이드바 설정 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    api_key = st.text_input(
        "Anthropic API 키",
        type="password",
        placeholder="sk-ant-...",
        help="https://console.anthropic.com 에서 발급받으세요"
    )

    st.markdown("---")
    st.markdown("### 📚 도움 방식")

    mode = st.radio(
        "어떻게 도와드릴까요?",
        ["🔍 풀이 보여주기", "💡 힌트만 주기", "📖 개념 설명", "✅ 내 풀이 확인"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🎓 학년·난이도")
    grade = st.selectbox(
        "학년",
        ["초등 1~2학년", "초등 3~4학년", "초등 5~6학년",
         "중학교 1학년", "중학교 2학년", "중학교 3학년",
         "고등학교 1학년", "고등학교 2학년", "고등학교 3학년",
         "대학교 / 그 이상"]
    )

    detail = st.select_slider(
        "설명 상세도",
        options=["간단히", "보통", "자세히"],
        value="보통"
    )

    st.markdown("---")
    st.caption("Made with ❤️ · Powered by Claude")

# ── 모드 파싱 ────────────────────────────────────────────────
MODE_MAP = {
    "🔍 풀이 보여주기": "solve",
    "💡 힌트만 주기":   "hint",
    "📖 개념 설명":     "explain",
    "✅ 내 풀이 확인":  "check",
}
current_mode = MODE_MAP[mode]

BADGE_MAP = {
    "solve":   ('<span class="badge badge-solve">풀이</span>',   "단계별 풀이를 제공합니다"),
    "hint":    ('<span class="badge badge-hint">힌트</span>',    "힌트만 드리고 직접 풀어보세요"),
    "explain": ('<span class="badge badge-explain">개념</span>', "관련 개념과 공식을 설명합니다"),
    "check":   ('<span class="badge badge-check">확인</span>',   "내 풀이의 정확성을 검토합니다"),
}

badge_html, mode_desc = BADGE_MAP[current_mode]

# ── 예시 문제 ────────────────────────────────────────────────
EXAMPLES = [
    "3x² - 5x + 2 = 0 을 풀어줘",
    "sin²θ + cos²θ = 1 증명해줘",
    "∫(2x + 3)dx 를 계산해줘",
    "피타고라스 정리를 설명해줘",
    "1부터 100까지의 합을 구해줘",
    "직각삼각형의 빗변이 5, 한 변이 3일 때 나머지 변의 길이",
]

# ── 메인 입력 영역 ───────────────────────────────────────────
st.markdown(f"""
<div class="card">
  {badge_html} <span style="color:#9ca3af; font-size:.87rem;">{mode_desc}</span>
</div>
""", unsafe_allow_html=True)

col_main, col_side = st.columns([3, 1])

with col_main:
    problem = st.text_area(
        "수학 문제를 입력하세요",
        placeholder="예: 3x² - 5x + 2 = 0 을 풀어줘\n\n수식, 한국어 모두 OK! 여러 문제도 한꺼번에 입력할 수 있어요.",
        height=160,
        label_visibility="collapsed"
    )

    # 내 풀이 확인 모드일 때 추가 입력
    my_answer = ""
    if current_mode == "check":
        my_answer = st.text_area(
            "내 풀이 / 답 입력",
            placeholder="여기에 내가 푼 풀이나 답을 입력하세요...",
            height=100,
        )

with col_side:
    st.markdown("**예시 문제**")
    for ex in EXAMPLES:
        if st.button(ex[:20] + ("…" if len(ex) > 20 else ""), key=ex, use_container_width=True):
            st.session_state["inject_example"] = ex
            st.rerun()

# 예시 자동 삽입
if "inject_example" in st.session_state:
    problem = st.session_state.pop("inject_example")

# ── 프롬프트 생성 ────────────────────────────────────────────
def build_prompt(mode, grade, detail, problem, my_answer=""):
    detail_map = {"간단히": "짧고 간결하게", "보통": "적당한 길이로", "자세히": "매우 상세하게"}
    detail_str = detail_map[detail]

    base = f"""당신은 친절하고 유능한 수학 선생님입니다. 학생은 {grade} 수준입니다.
설명은 {detail_str} 해주세요. 수식은 명확하게 표현하고, 단계마다 이유를 설명해 주세요.
한국어로 답변해 주세요.\n\n"""

    if mode == "solve":
        return base + f"다음 수학 문제를 단계별로 풀어주세요:\n\n{problem}"
    elif mode == "hint":
        return base + f"다음 문제를 직접 풀지 말고, 학생 스스로 풀 수 있도록 핵심 힌트만 2~3개 제공해주세요:\n\n{problem}"
    elif mode == "explain":
        return base + f"다음 문제와 관련된 수학 개념, 공식, 원리를 설명해주세요. 예제도 1~2개 포함해주세요:\n\n{problem}"
    elif mode == "check":
        return base + f"""다음 문제에 대한 학생의 풀이를 검토해주세요.
맞은 부분은 칭찬하고, 틀린 부분은 어디서 왜 틀렸는지 친절하게 설명해주세요.

[문제]
{problem}

[학생 풀이]
{my_answer}"""

# ── 실행 버튼 ────────────────────────────────────────────────
st.markdown("")
run_col, _ = st.columns([1, 3])
with run_col:
    run = st.button("✨ 도움 요청하기", use_container_width=True)

st.markdown("---")

# ── 결과 출력 ────────────────────────────────────────────────
if run:
    if not api_key:
        st.error("🔑 왼쪽 사이드바에서 Anthropic API 키를 먼저 입력해 주세요.")
        st.stop()
    if not problem.strip():
        st.warning("📝 문제를 입력해 주세요!")
        st.stop()
    if current_mode == "check" and not my_answer.strip():
        st.warning("✏️ 내 풀이도 입력해 주세요!")
        st.stop()

    prompt = build_prompt(current_mode, grade, detail, problem.strip(), my_answer.strip())

    try:
        client = anthropic.Anthropic(api_key=api_key)

        result_placeholder = st.empty()
        full_text = ""

        with st.spinner("🤔 풀이 중..."):
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    result_placeholder.markdown(
                        f'<div class="result-box">{full_text}▌</div>',
                        unsafe_allow_html=True
                    )

        result_placeholder.markdown(
            f'<div class="result-box">{full_text}</div>',
            unsafe_allow_html=True
        )

        # 세션에 기록 저장
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.insert(0, {
            "mode": mode,
            "problem": problem.strip()[:60],
            "answer": full_text,
        })

    except anthropic.AuthenticationError:
        st.error("❌ API 키가 올바르지 않습니다. 다시 확인해 주세요.")
    except anthropic.RateLimitError:
        st.error("⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# ── 이전 기록 ────────────────────────────────────────────────
if "history" in st.session_state and st.session_state.history:
    with st.expander(f"📋 이전 질문 기록 ({len(st.session_state.history)}개)", expanded=False):
        for i, item in enumerate(st.session_state.history[:5]):
            st.markdown(f"**{i+1}. [{item['mode']}]** {item['problem']}{'…' if len(item['problem'])>=60 else ''}")
            st.markdown(f'<div class="result-box" style="font-size:.9rem;">{item["answer"][:400]}{"…" if len(item["answer"])>400 else ""}</div>', unsafe_allow_html=True)
            st.markdown("")
