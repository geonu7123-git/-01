import streamlit as st
import sympy as sp
from sympy import *
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

st.set_page_config(page_title="수학 숙제 도우미", page_icon="🧮", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #0f1117; color: #e8eaf0; }
.hero { text-align:center; padding: 2rem 1rem 1rem; }
.hero h1 { font-size:2.4rem; font-weight:700;
  background: linear-gradient(135deg,#7c6af7,#5eead4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color:#9ca3af; }
.step { background:#1a1d27; border:1px solid #2a2d3d; border-radius:10px;
  padding:.8rem 1.2rem; margin:.4rem 0; }
.step-num { color:#7c6af7; font-weight:700; }
.stButton>button { background:linear-gradient(135deg,#7c6af7,#5eead4)!important;
  color:#0f1117!important; font-weight:700!important; border:none!important;
  border-radius:10px!important; padding:.5rem 1.5rem!important; }
.stButton>button:hover { opacity:.85!important; }
.stTextArea textarea { background:#1a1d27!important; border:1px solid #2a2d3d!important;
  border-radius:10px!important; color:#e8eaf0!important; }
hr { border-color:#2a2d3d!important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🧮 수학 숙제 도우미</h1><p>방정식 · 미적분 · 인수분해 · 연립방정식 등을 자동으로 풀어드려요 (API 불필요)</p></div>', unsafe_allow_html=True)

x, y, z, t, n = symbols('x y z t n')
a, b, c, d = symbols('a b c d')
f, g, h, k, m, p, q, r, s_sym, u, v, w = symbols('f g h k m p q r s u v w')
TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# 알파벳 전체를 심볼로 등록 (함수명·상수 제외)
_ALL_SYMBOLS = {ch: symbols(ch) for ch in 'abcdfghjklmnopqrstuvwxyz'}
LOCAL_DICT = {
    **_ALL_SYMBOLS,
    'e':E,'pi':pi,'sin':sin,'cos':cos,'tan':tan,'log':log,'ln':ln,
    'sqrt':sqrt,'exp':exp,'abs':Abs,'oo':oo,'inf':oo,
    'asin':asin,'acos':acos,'atan':atan,'sinh':sinh,'cosh':cosh,'tanh':tanh,
}

def safe_parse(s):
    s = s.strip().replace("^", "**")
    # 숫자 뒤 문자: 2x → 2*x
    s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
    # 문자 뒤 숫자: x2 → x**2  (단, ** 바로 뒤는 제외)
    s = re.sub(r'(?<!\*\*)([a-zA-Z])(\d)', r'\1**\2', s)
    return parse_expr(s, transformations=TRANSFORMATIONS, local_dict=LOCAL_DICT)

def solve_equation(eq_str):
    steps = []
    if '=' not in eq_str:
        eq_str += " = 0"
    p = eq_str.split('=', 1)
    lhs, rhs = safe_parse(p[0]), safe_parse(p[1])
    eq = Eq(lhs, rhs)
    steps.append(("📌 방정식", f"$${latex(eq)}$$"))

    expr = lhs - rhs

    # 차수 표시 (다항식일 때만)
    try:
        deg = Poly(expr, x).degree()
        steps.append(("📊 차수", f"{deg}차 방정식"))
    except: pass

    solutions = []

    # 1단계: 일반 solve
    try:
        solutions = solve(eq, x)
    except: pass

    # 2단계: solveset (복소수 포함)
    if not solutions:
        try:
            ss = solveset(eq, x, domain=Reals)
            if ss and not ss.is_empty and isinstance(ss, (FiniteSet,)):
                solutions = list(ss)
        except: pass

    # 3단계: 로그 변환 시도 (지수방정식 x^x = a^b 형태)
    if not solutions:
        try:
            # 양변 log 취하기
            log_lhs = expand_log(log(lhs), force=True)
            log_rhs = expand_log(log(rhs), force=True)
            log_eq = Eq(log_lhs, log_rhs)
            steps.append(("🔄 로그 변환", f"양변에 자연로그를 취합니다:  \n$$\\ln({latex(lhs)}) = \\ln({latex(rhs)})$$  \n$$\\Rightarrow {latex(log_lhs)} = {latex(log_rhs)}$$"))
            log_solutions = solve(log_eq, x)
            if log_solutions:
                solutions = log_solutions
        except: pass

    # 4단계: 수치해 (nsolve) - 해석적 풀이 불가 시
    if not solutions:
        try:
            steps.append(("🔄 수치 풀이", "해석적 풀이가 어려워 수치 방법으로 근사해를 구합니다."))
            for x0 in [1, 2, 3, 5, 10, 0.5, -1, -2]:
                try:
                    ns = nsolve(expr, x, x0)
                    # 중복 제거 (오차 범위 내)
                    if not any(abs(float(ns) - float(s)) < 1e-6 for s in solutions):
                        solutions.append(ns)
                    if len(solutions) >= 3:
                        break
                except: pass
        except: pass

    # 결과 출력
    if not solutions:
        steps.append(("❌ 해", "실수 범위에서 해를 구할 수 없습니다."))
    else:
        formatted = []
        for s in solutions:
            s_simplified = simplify(s)
            line = f"$$x = {latex(s_simplified)}$$"
            # 수치값도 함께 표시
            try:
                numeric = float(s_simplified.evalf())
                if s_simplified != numeric:
                    line += f"  \n$\\approx {numeric:.6f}$"
            except: pass
            formatted.append(line)
        steps.append(("✅ 해", "  \n".join(formatted)))

        # 검산
        checks = []
        for s in solutions:
            try:
                lv = simplify(lhs.subs(x, s))
                rv = simplify(rhs.subs(x, s))
                diff_val = simplify(lv - rv)
                ok = "✓" if diff_val == 0 or abs(float(diff_val.evalf())) < 1e-6 else "△ (근사값)"
                checks.append(f"$x = {latex(simplify(s))}$ 대입 → 좌변 $\\approx {latex(lv)}$, 우변 $\\approx {latex(rv)}$ {ok}")
            except: pass
        if checks:
            steps.append(("🔎 검산", "  \n".join(checks)))

    return steps

def factorize_expr(expr_str):
    steps = []
    expr = safe_parse(expr_str)
    steps.append(("📌 입력 식", f"$${latex(expr)}$$"))
    steps.append(("🔄 전개 형태", f"$${latex(expand(expr))}$$"))
    steps.append(("✅ 인수분해", f"$${latex(factor(expr))}$$"))
    return steps

def differentiate_expr(expr_str, var_str="x"):
    steps = []
    expr = safe_parse(expr_str)
    var = symbols(var_str)
    steps.append(("📌 함수", f"$$f({var}) = {latex(expr)}$$"))
    if isinstance(expr, Add):
        parts_d = [f"$$\\frac{{d}}{{d{var}}}\\left[{latex(term)}\\right] = {latex(diff(term, var))}$$"
                   for term in expr.args]
        steps.append(("🔄 항별 미분", "  \n".join(parts_d)))
    result = simplify(diff(expr, var))
    steps.append(("✅ 미분 결과", f"$$f'({var}) = {latex(result)}$$"))
    steps.append(("📈 2차 미분", f"$$f''({var}) = {latex(simplify(diff(expr, var, 2)))}$$"))
    return steps

def integrate_expr(expr_str, var_str="x", lower=None, upper=None):
    steps = []
    expr = safe_parse(expr_str)
    var = symbols(var_str)
    steps.append(("📌 함수", f"$$f({var}) = {latex(expr)}$$"))
    if lower and upper:
        lo, hi = safe_parse(lower), safe_parse(upper)
        steps.append(("📐 정적분 설정", f"$$\\int_{{{latex(lo)}}}^{{{latex(hi)}}} {latex(expr)}\\,d{var}$$"))
        result = simplify(integrate(expr, (var, lo, hi)))
        steps.append(("✅ 결과", f"$$= {latex(result)}$$"))
        try:
            steps.append(("🔢 근삿값", f"≈ {float(result.evalf()):.6f}"))
        except: pass
    else:
        result = integrate(expr, var)
        steps.append(("✅ 부정적분", f"$$\\int {latex(expr)}\\,d{var} = {latex(result)} + C$$"))
        steps.append(("🔎 검증 (미분)", f"$$\\frac{{d}}{{d{var}}}[{latex(result)}] = {latex(simplify(diff(result, var)))}$$"))
    return steps

def solve_system(text):
    steps = []
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    eqs = []
    for line in lines:
        if '=' in line:
            p = line.split('=', 1)
            eqs.append(Eq(safe_parse(p[0]), safe_parse(p[1])))
        else:
            eqs.append(Eq(safe_parse(line), 0))
    steps.append(("📌 연립방정식", "  \n".join([f"$${latex(e)}$$" for e in eqs])))
    all_vars = set()
    for e in eqs:
        all_vars |= e.free_symbols
    solution = solve(eqs, list(all_vars))
    if not solution:
        steps.append(("❌ 결과", "해가 없거나 무한히 많습니다."))
    elif isinstance(solution, dict):
        steps.append(("✅ 해", "  \n".join([f"$${latex(k)} = {latex(v)}$$" for k, v in solution.items()])))
    else:
        steps.append(("✅ 해", str(solution)))
    return steps

def expand_simplify(expr_str):
    steps = []
    expr = safe_parse(expr_str)
    steps.append(("📌 입력", f"$${latex(expr)}$$"))
    steps.append(("🔄 전개", f"$${latex(expand(expr))}$$"))
    steps.append(("✅ 간소화", f"$${latex(simplify(expr))}$$"))
    ts = trigsimp(expr)
    if ts != simplify(expr):
        steps.append(("📐 삼각함수 간소화", f"$${latex(ts)}$$"))
    return steps

def compute_limit(expr_str, var_str, point_str, direction="+"):
    steps = []
    expr, var, point = safe_parse(expr_str), symbols(var_str), safe_parse(point_str)
    steps.append(("📌 함수", f"$$f({var}) = {latex(expr)}$$"))
    steps.append(("🎯 극한점", f"$${var} \\to {latex(point)}$$"))
    result = limit(expr, var, point, direction)
    dir_sym = "^{+}" if direction == "+" else "^{-}"
    steps.append(("✅ 극한값", f"$$\\lim_{{{var} \\to {latex(point)}{dir_sym}}} {latex(expr)} = {latex(result)}$$"))
    return steps

def auto_solve(text):
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    if len(lines) >= 2 and all('=' in l for l in lines):
        return "연립방정식", solve_system(text)
    kw = text.lower()
    if any(k in kw for k in ["미분", "d/dx", "derivative"]):
        m = re.sub(r"(미분|d/dx|derivative|해줘|구해줘|하면|을|를|의|\?)", "", text).strip()
        return "미분", differentiate_expr(m)
    if any(k in kw for k in ["적분", "integral"]):
        m = re.sub(r"(적분|integral|해줘|구해줘|하면|을|를|의|\?)", "", text).strip()
        return "적분", integrate_expr(m)
    if any(k in kw for k in ["인수분해", "factor"]):
        m = re.sub(r"(인수분해|factor|해줘|하면|을|를|의|\?)", "", text).strip()
        return "인수분해", factorize_expr(m)
    if any(k in kw for k in ["전개", "expand"]):
        m = re.sub(r"(전개|expand|해줘|하면|을|를|의|\?)", "", text).strip()
        return "전개", expand_simplify(m)
    if '=' in text:
        return "방정식", solve_equation(text)
    return "계산/간소화", expand_simplify(text)

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 기능 선택")
    mode = st.radio("풀이 방식", [
        "🤖 자동 감지", "📐 방정식 풀기", "🔢 연립방정식",
        "➗ 인수분해", "📈 미분", "∫ 적분", "🔄 전개/간소화", "🎯 극한"
    ])
    int_lower = int_upper = ""
    lim_var = "x"; lim_point = "0"; lim_dir = "양쪽(+)"
    if "∫ 적분" in mode:
        st.markdown("---")
        st.markdown("**정적분 범위** (비우면 부정적분)")
        int_lower = st.text_input("하한", placeholder="0")
        int_upper = st.text_input("상한", placeholder="1")
    if "🎯 극한" in mode:
        st.markdown("---")
        lim_var = st.text_input("변수", value="x")
        lim_point = st.text_input("극한점", placeholder="0 또는 oo")
        lim_dir = st.radio("방향", ["양쪽(+)", "오른쪽(+)", "왼쪽(-)"])
    st.markdown("---")
    st.markdown("**입력 형식**")
    st.markdown("- 곱셈: `2*x` 또는 `2x`\n- 거듭제곱: `x**2` 또는 `x^2`\n- 루트: `sqrt(x)`\n- 삼각: `sin(x)`, `cos(x)`\n- 로그: `log(x)`, `ln(x)`\n- 무한: `oo`\n- 연립: 줄 바꿔서 입력")
    st.caption("SymPy 기반 · API 불필요")

# ── 예시 ──────────────────────────────────────────────────────
EXAMPLES = {
    "방정식":     ["x**2 - 5*x + 6 = 0", "2*x**2 + 3*x - 2 = 0", "x**3 - 6*x**2 + 11*x - 6 = 0"],
    "지수방정식": ["x^x = 3^324", "2^x = 32", "x^x = 4^8"],
    "연립방정식": ["2*x + y = 5\nx - y = 1", "x + y + z = 6\n2*x - y + z = 3\nx + 2*y - z = 2"],
    "문자식":     ["a^3 * b^5", "(a+b)^2", "a^3 * b^5 + a^2 * b^3"],
    "인수분해":   ["x**2 - 5*x + 6", "x**3 - 8", "4*x**2 - 12*x + 9"],
    "미분":       ["x**3 + 2*x**2 - 5*x + 1", "sin(x)*cos(x)", "exp(x)*log(x)"],
    "적분":       ["2*x + 3", "sin(x)", "x**2 + 3*x"],
    "전개":       ["(x+2)**3", "(a+b)**4", "(x-1)*(x+2)*(x+3)"],
}

# 예시 클릭값을 text_area value로 미리 꺼내두기
prefill = st.session_state.pop("ex", "")
auto_run = st.session_state.pop("auto_run", False)

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_area("수식 입력", height=140,
        value=prefill,
        placeholder="예) 방정식: x**2 - 5*x + 6 = 0\n    미분/적분: x**3 + 2*x\n    연립: 2*x + y = 5  (줄 바꿔서 입력)",
        label_visibility="collapsed")
with col2:
    st.markdown("**예시 클릭**")
    for cat, exs in EXAMPLES.items():
        with st.expander(cat):
            for ex in exs:
                label = ex.split('\n')[0][:22] + ("…" if len(ex.split('\n')[0]) > 22 else "")
                if st.button(label, key=ex):
                    st.session_state["ex"] = ex
                    st.session_state["auto_run"] = True
                    st.rerun()

btn_col, _ = st.columns([1, 5])
with btn_col:
    run = st.button("✨ 풀기", use_container_width=True)

st.markdown("---")

# ── 실행 (버튼 클릭 또는 예시 자동 실행) ──────────────────────
if run or auto_run:
    if not user_input.strip():
        st.warning("📝 수식을 입력해 주세요!")
        st.stop()
    try:
        with st.spinner("🤔 계산 중..."):
            if "자동 감지" in mode:
                title, steps = auto_solve(user_input)
            elif "방정식" in mode and "연립" not in mode:
                title, steps = "방정식", solve_equation(user_input)
            elif "연립" in mode:
                title, steps = "연립방정식", solve_system(user_input)
            elif "인수분해" in mode:
                title, steps = "인수분해", factorize_expr(user_input)
            elif "미분" in mode:
                title, steps = "미분", differentiate_expr(user_input)
            elif "∫ 적분" in mode:
                title, steps = "적분", integrate_expr(user_input,
                    lower=int_lower.strip() or None, upper=int_upper.strip() or None)
            elif "전개" in mode:
                title, steps = "전개/간소화", expand_simplify(user_input)
            elif "극한" in mode:
                title, steps = "극한", compute_limit(user_input, lim_var, lim_point,
                    "-" if "왼쪽" in lim_dir else "+")
            else:
                title, steps = auto_solve(user_input)

        st.markdown(f"### 📋 {title} 풀이")
        for i, (label, content) in enumerate(steps, 1):
            st.markdown(
                f'<div class="step"><span class="step-num">Step {i}</span> &nbsp; <strong>{label}</strong></div>',
                unsafe_allow_html=True)
            st.markdown(content)
            st.markdown("")

        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.insert(0, {"input": user_input[:50], "title": title})

    except Exception as e:
        st.error(f"❌ 풀이 오류: `{e}`")
        st.info("💡 **팁:** 곱셈 `*`, 거듭제곱 `**` 또는 `^`, 분수 `1/2`, 루트 `sqrt(x)`")

if st.session_state.get("history"):
    with st.expander(f"📋 이전 풀이 기록 ({len(st.session_state.history)}개)"):
        for i, h in enumerate(st.session_state.history[:8], 1):
            st.markdown(f"**{i}.** [{h['title']}] `{h['input']}`")
