import streamlit as st
import requests
import uuid
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="AI-Шеф Про", page_icon="👨‍🍳", layout="wide")

# =====================================================================
# 🎨 КАСТОМНЫЙ ДИЗАЙН (ОБЪЕМНЫЙ ФОН, СТЕКЛЯННЫЕ КАРТОЧКИ, КНОПКИ)
# =====================================================================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 15% 20%, #2a1b3d 0%, transparent 45%),
                radial-gradient(circle at 85% 80%, #162447 0%, transparent 45%),
                #0d111a;
    color: #f8fafc;
}
[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.85);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(26, 32, 48, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 8px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(10px);
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #ff6b35 0%, #f72585 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.65rem 1.2rem;
    font-weight: 700;
    font-size: 16px;
    box-shadow: 0 4px 15px rgba(247, 37, 133, 0.35);
    transition: all 0.2s ease;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(247, 37, 133, 0.55);
}
[data-testid="stImage"] img {
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
}
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 14px;
    border-radius: 14px;
    backdrop-filter: blur(8px);
}
</style>
""", unsafe_allow_html=True)

AUTH_URL = "https://" + "ngw.devices.sberbank.ru:9443" + "/api/v2/oauth"
API_URL = "https://" + "gigachat.devices.sberbank.ru" + "/api/v1/chat/completions"

if "history" not in st.session_state:
    st.session_state.history = []

def get_gigachat_token(auth_key: str) -> str:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_key.strip()}"
    }
    r = requests.post(AUTH_URL, headers=headers, data={"scope": "GIGACHAT_API_PERS"}, verify=False, timeout=20)
    if r.status_code != 200 or not r.text.strip():
        raise ValueError(f"Ошибка авторизации Сбера (код {r.status_code}). Проверьте ключ и пакет токенов.")
    return r.json()["access_token"]

def fetch_recipe(auth_key: str, ingredients: list, meal: str, time_lim: str, wishes: str) -> dict:
    token = get_gigachat_token(auth_key)
    sys_prompt = (
        "Ты профессиональный повар. Придумай вкусное блюдо из переданных продуктов (можно добавить соль, перец, воду, масло, сахар). "
        "Оформи ответ строго по меткам:\n"
        "TITLE: Название блюда\n"
        "KEYWORD: 2-3 слова на английском для фото блюда\n"
        "TIME: Время готовки\n"
        "DIFF: Сложность (Легко/Средне/Сложно)\n"
        "CAL: Калории на 100г\n"
        "MACROS: Б: ... | Ж: ... | У: ...\n"
        "INGREDIENTS:\n- Ингредиент с граммовкой\n"
        "STEPS:\n1. Шаг приготовления\n"
        "TIP: Короткий совет шефа"
    )
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Прием пищи: {meal}. Время: {time_lim}. Пожелания: {wishes or 'Нет'}."
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt}
        ],
        "temperature": 0.7
    }
    r = requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=35)
    if not r.text.strip():
        raise ValueError(f"GigaChat вернул пустой ответ (HTTP {r.status_code}). Попробуйте нажать кнопку еще раз.")
    r.raise_for_status()

    first_choice = r.json()["choices"].pop(0)
    text = first_choice["message"]["content"]

    data = {
        "title": "Блюдо от шефа", "keyword": "delicious food", "time": time_lim,
        "diff": "Средне", "cal": "Не указано", "macros": "Сбалансировано",
        "ings": [], "steps": [], "tip": ""
    }
    mode = None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("TITLE:"): data["title"] = s[6:].strip().strip('"«»*')
        elif s.startswith("KEYWORD:"): data["keyword"] = s[8:].strip()
        elif s.startswith("TIME:"): data["time"] = s[5:].strip()
        elif s.startswith("DIFF:"): data["diff"] = s[5:].strip()
        elif s.startswith("CAL:"): data["cal"] = s[4:].strip()
        elif s.startswith("MACROS:"): data["macros"] = s[7:].strip()
        elif s.startswith("TIP:"): data["tip"] = s[4:].strip()
        elif s.startswith("INGREDIENTS:"): mode = "ing"
        elif s.startswith("STEPS:"): mode = "step"
        elif mode == "ing": data["ings"].append(s.lstrip("-•* ").strip())
        elif mode == "step": data["steps"].append(s.lstrip("0123456789.) ").strip())

    if not data["steps"]:
        data["steps"] = [text]
    return data

# =====================================================================
# 🧭 БОКОВАЯ ПАНЕЛЬ (SECRETS И КЛИКАБЕЛЬНАЯ ИСТОРИЯ)
# =====================================================================
with st.sidebar:
    st.header("🔑 Настройки")
    saved_key = st.secrets.get("GIGACHAT_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("GigaChat Authorization Key:", value=saved_key, type="password")

    st.divider()
    st.header("📜 История блюд")
    if not st.session_state.history:
        st.caption("Здесь появятся ваши сгенерированные рецепты.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            if st.button(f"🍽️ {item['title']}", key=f"hist_{idx}", use_container_width=True):
                st.session_state.current = item

st.title("👨‍🍳 AI-Шеф Про: Генератор рецептов")
st.caption("Умный подбор блюд из ваших продуктов с расчетом КБЖУ и визуализацией")

col1, col2 = st.columns([1, 1.3], gap="large")

with col1:
    with st.container(border=True):
        st.subheader("1. Продукты в наличии")
        catalog = {
            "🥩 Мясо и рыба": ["Куриное филе", "Говядина", "Свинина", "Фарш", "Рыба", "Яйца", "Сосиски", "Тунец"],
            "🥦 Овощи": ["Картофель", "Лук", "Морковь", "Помидоры", "Огурцы", "Чеснок", "Шампиньоны", "Капуста"],
            "🧀 Молочка": ["Молоко", "Сыр твердый", "Сметана", "Сливочное масло", "Творог", "Сливки"],
            "🌾 Крупы и мучное": ["Рис", "Макароны", "Гречка", "Овсянка", "Мука", "Хлеб", "Лаваш"]
        }
        selected = []
        for tab, (cat, items) in zip(st.tabs(list(catalog.keys())), catalog.items()):
            with tab:
                cols = st.columns(2)
                for i, prod in enumerate(items):
                    if cols[i % 2].checkbox(prod, key=f"p_{prod}"):
                        selected.append(prod)

        custom = st.text_input("➕ Свои продукты (через запятую):")
        if custom:
            selected.extend([x.strip() for x in custom.split(",") if x.strip()])
        if selected:
            st.info(f"**Выбрано ({len(selected)}):** {', '.join(selected)}")

        st.divider()
        st.subheader("2. Параметры")
        c1, c2 = st.columns(2)
        meal = c1.selectbox("Прием пищи:", ["Любой", "Завтрак", "Обед", "Ужин", "Перекус"])
        time_lim = c2.selectbox("Время:", ["Не важно", "До 15 мин", "До 30 мин", "До 1 часа"])
        wishes = st.text_input("✨ Пожелания (ПП, без жарки и т.д.):")
        btn = st.button("🔥 Придумать рецепт", type="primary", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("🍽️ Готовый рецепт")
        if btn:
            if not api_key:
                st.error("⚠️ Введите Authorization Key в меню слева!")
            elif not selected:
                st.error("⚠️ Выберите хотя бы один продукт!")
            else:
                with st.spinner("Шеф-повар готовит рецепт..."):
                    try:
                        res = fetch_recipe(api_key, selected, meal, time_lim, wishes)
                        st.session_state.history.append(res)
                        st.session_state.current = res
                    except Exception as e:
                        st.error(f"🚨 Ошибка: {e}")

        if "current" in st.session_state:
            rec = st.session_state.current
            st.markdown(f"## {rec['title']}")

            kw = urllib.parse.quote(f"delicious {rec['keyword']}, professional food photography, appetizing, 4k")
            img_url = "https://" + "image.pollinations.ai/prompt/" + kw + "?width=800&height=450&nologo=true"
            st.image(img_url, use_container_width=True)

            m1, m2, m3 = st.columns(3)
            m1.metric("⏱️ Время", rec["time"])
            m2.metric("📊 Сложность", rec["diff"])
            m3.metric("🔥 Калории", rec["cal"])
            st.caption(f"**БЖУ:** {rec['macros']}")
            st.divider()

            st.markdown("### 🛒 Ингредиенты:")
            for ing in rec["ings"]:
                st.markdown(f"- {ing}")

            st.markdown("### 👨‍🍳 Приготовление:")
            for i, step in enumerate(rec["steps"], 1):
                st.markdown(f"**{i}.** {step}")

            if rec["tip"]:
                st.success(f"💡 **Совет шефа:** {rec['tip']}")

            txt = f"{rec['title']}\n\nИнгредиенты:\n" + "\n".join(rec["ings"]) + "\n\nШаги:\n" + "\n".join(rec["steps"])
            st.download_button("📥 Скачать рецепт (.txt)", txt, file_name="recipe.txt", use_container_width=True)
        else:
            st.markdown("""
