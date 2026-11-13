import streamlit as st
import requests
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="AI-Шеф Про", page_icon="👨‍🍳", layout="wide")

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 15% 20%, #2a1b3d 0%, transparent 45%),
                radial-gradient(circle at 85% 80%, #162447 0%, transparent 45%), #0d111a;
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
    max-height: 400px;
    width: 100%;
    object-fit: cover;
}
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 12px;
    border-radius: 14px;
    backdrop-filter: blur(8px);
}
</style>
""", unsafe_allow_html=True)

AUTH_URL = "https://" + "ngw.devices.sberbank.ru:9443" + "/api/v2/oauth"
API_URL = "https://" + "gigachat.devices.sberbank.ru" + "/api/v1/chat/completions"

if "history" not in st.session_state:
    st.session_state.history = []

@st.cache_data(ttl=1500, show_spinner=False)
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

def find_dish_photo(keyword: str) -> str:
    m = "https://" + "www.themealdb." + "com/images/media/meals/"
    photos = {
        "chicken": m + "wyxwsp1486979827.jpg",
        "beef": m + "sytuqu1511553755.jpg",
        "steak": m + "vussxq1511882648.jpg",
        "pasta": m + "ustsqw1468250014.jpg",
        "salad": m + "wvpsxx1468256321.jpg",
        "lasagna": m + "wtsvxx1511296896.jpg",
        "fish": m + "1548772327.jpg",
        "soup": m + "1529446352.jpg",
        "pancake": m + "rwuyqx1511383174.jpg",
        "egg": m + "1550441882.jpg",
        "rice": m + "xxpqsy1511452222.jpg",
        "potato": m + "vrspxv1511722107.jpg",
        "sandwich": m + "xr0n4r1576788363.jpg",
        "dessert": m + "wyrqqq1468233628.jpg"
    }
    kw = keyword.lower()
    for key, url in photos.items():
        if key in kw:
            return url
    return photos["chicken"]
def call_gigachat(auth_key: str, sys_prompt: str, usr_prompt: str) -> str:
    token = get_gigachat_token(auth_key)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": usr_prompt}],
        "temperature": 0.9
    }
    r = requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=40)
    if not r.text.strip():
        raise ValueError(f"GigaChat вернул пустой ответ (HTTP {r.status_code}). Попробуйте нажать кнопку еще раз.")
    r.raise_for_status()
    return r.json()["choices"].pop(0)["message"]["content"]

def fetch_single_recipe(auth_key: str, ingredients: list, meal: str, time_lim: str, wishes: str, sport_mode: bool, past_titles: list) -> dict:
    sport_rule = "РЕЖИМ СПОРТ-ПИТАНИЯ: сделай максимальный акцент на высоком содержании белка, минимуме жиров/масла и точном подсчете граммов белка на порцию. " if sport_mode else ""
    sys_prompt = (
        "Ты креативный шеф-повар. Придумай оригинальное вкусное блюдо строго из переданных продуктов (можно добавить соль, перец, воду, масло, сахар). "
        f"{sport_rule}"
        "ВАЖНО: придумывай разнообразные форматы (вок, рагу, паста, рулеты, супы, теплые салаты, стир-фрай, сэндвичи, стейк, лазанья) и НЕ предлагай запеканки или омлеты, если об этом прямо не просят. "
        "Оцени среднюю стоимость использованной граммовки продуктов в рублях по ценам магазинов России. "
        "Оформи ответ строго с новой строки для каждой метки без символов # и *:\n"
        "TITLE: Название блюда\nKEYWORD: 1 слово на английском (chicken, beef, steak, pasta, salad, lasagna, fish, soup, pancake, egg, rice, potato, sandwich, dessert)\n"
        "TIME: Время готовки\nDIFF: Сложность (Легко/Средне/Сложно)\nCAL: Калории на 100г\nCOST: Общая примерная цена блюда в рублях (например: ~290 ₽)\n"
        "MACROS: Б: ... | Ж: ... | У: ...\n"
        "INGREDIENTS:\n- Ингредиент с граммовкой (~цена ₽ за это количество)\nSTEPS:\n1. Шаг приготовления\nTIP: Короткий совет шефа\n"
        "PAIRING: Идеальный соус, гарнир или напиток к этому блюду"
    )
    avoid_text = f" Не повторяй эти блюда: {', '.join(past_titles)}." if past_titles else ""
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Прием пищи: {meal}. Время: {time_lim}. Пожелания: {wishes or 'Нет'}.{avoid_text}"
    text = call_gigachat(auth_key, sys_prompt, usr_prompt)

    data = {
        "mode": "single", "title": "Блюдо от шефа", "keyword": "chicken", "time": time_lim,
        "diff": "Средне", "cal": "Не указано", "cost": "~250 ₽", "macros": "Сбалансировано",
        "ings": [], "steps": [], "tip": "", "pairing": "", "photo": ""
    }
    mode = None
    for line in text.splitlines():
        s = line.strip().lstrip("#* ").rstrip("*")
        if not s: continue
        if "TITLE:" in s: data["title"] = s.split("TITLE:", 1).pop().strip().strip('"«»*')
        elif "KEYWORD:" in s: data["keyword"] = s.split("KEYWORD:", 1).pop().strip().strip('*')
        elif "TIME:" in s: data["time"] = s.split("TIME:", 1).pop().strip().strip('*')
        elif "DIFF:" in s: data["diff"] = s.split("DIFF:", 1).pop().strip().strip('*')
        elif "CAL:" in s: data["cal"] = s.split("CAL:", 1).pop().strip().strip('*')
        elif "COST:" in s: data["cost"] = s.split("COST:", 1).pop().strip().strip('*')
        elif "MACROS:" in s: data["macros"] = s.split("MACROS:", 1).pop().strip().strip('*')
        elif "TIP:" in s: data["tip"] = s.split("TIP:", 1).pop().strip().strip('*')
        elif "PAIRING:" in s: data["pairing"] = s.split("PAIRING:", 1).pop().strip().strip('*')
        elif "INGREDIENTS:" in s: mode = "ing"
        elif "STEPS:" in s: mode = "step"
        elif mode == "ing": data["ings"].append(s.lstrip("-•* ").strip())
        elif mode == "step": data["steps"].append(s.lstrip("0123456789.) ").strip())

    if not data["steps"]:
        data["steps"] = [text]
    data["photo"] = find_dish_photo(data["keyword"])
    return data

def fetch_day_ration(auth_key: str, ingredients: list, wishes: str, sport_mode: bool) -> dict:
    sport_rule = "Упор на высокий белок и чистый состав. " if sport_mode else ""
    sys_prompt = (
        "Ты диетолог и шеф-повар. Составь сбалансированный рацион на целый день (Завтрак, Обед, Ужин) максимально используя переданные продукты (можно добавить базовые специи, воду, масло, крупы). "
        f"{sport_rule}Рассчитай примерную стоимость каждого приема пищи и общий итог в рублях. "
        "Оформи ответ строго с новой строки для каждой метки без символов # и *:\n"
        "TOTAL_COST: Общий бюджет за день (например: ~620 ₽)\n"
        "TOTAL_CAL: Общая калорийность за день (например: ~1850 ккал)\n"
        "TOTAL_MACROS: Б: ...г | Ж: ...г | У: ...г\n"
        "BREAKFAST_TITLE: Название завтрака\nBREAKFAST_INFO: Краткий состав, граммовка, цена (~150 ₽) и 3-4 шага приготовления\n"
        "LUNCH_TITLE: Название обеда\nLUNCH_INFO: Краткий состав, граммовка, цена (~270 ₽) и 3-4 шага приготовления\n"
        "DINNER_TITLE: Название ужина\nDINNER_INFO: Краткий состав, граммовка, цена (~200 ₽) и 3-4 шага приготовления\n"
        "TIP: Совет диетолога на день"
    )
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Пожелания: {wishes or 'Сбалансированное питание'}."
    text = call_gigachat(auth_key, sys_prompt, usr_prompt)

    data = {
        "mode": "day", "title": "Рацион на день", "cost": "~600 ₽", "cal": "~1800 ккал",
        "macros": "Сбалансировано", "b_title": "Завтрак", "b_info": "",
        "l_title": "Обед", "l_info": "", "d_title": "Ужин", "d_info": "", "tip": "", "raw": text
    }
    curr = None
    for line in text.splitlines():
        s = line.strip().lstrip("#* ").rstrip("*")
        if not s: continue
        if "TOTAL_COST:" in s: data["cost"] = s.split("TOTAL_COST:", 1).pop().strip().strip('*')
        elif "TOTAL_CAL:" in s: data["cal"] = s.split("TOTAL_CAL:", 1).pop().strip().strip('*')
        elif "TOTAL_MACROS:" in s: data["macros"] = s.split("TOTAL_MACROS:", 1).pop().strip().strip('*')
        elif "BREAKFAST_TITLE:" in s:
            data["b_title"] = s.split("BREAKFAST_TITLE:", 1).pop().strip().strip('"«»*')
            curr = "b"
        elif "BREAKFAST_INFO:" in s:
            data["b_info"] = s.split("BREAKFAST_INFO:", 1).pop().strip()
            curr = "b"
        elif "LUNCH_TITLE:" in s:
            data["l_title"] = s.split("LUNCH_TITLE:", 1).pop().strip().strip('"«»*')
            curr = "l"
        elif "LUNCH_INFO:" in s:
            data["l_info"] = s.split("LUNCH_INFO:", 1).pop().strip()
            curr = "l"
        elif "DINNER_TITLE:" in s:
            data["d_title"] = s.split("DINNER_TITLE:", 1).pop().strip().strip('"«»*')
            curr = "d"
        elif "DINNER_INFO:" in s:
            data["d_info"] = s.split("DINNER_INFO:", 1).pop().strip()
            curr = "d"
        elif "TIP:" in s:
            data["tip"] = s.split("TIP:", 1).pop().strip().strip('*')
            curr = None
        elif curr == "b": data["b_info"] += "\n" + s
        elif curr == "l": data["l_info"] += "\n" + s
        elif curr == "d": data["d_info"] += "\n" + s

    data["title"] = f"Рацион ({data['cost']})"
    return data

with st.sidebar:
    st.header("🔑 Настройки")
    saved_key = st.secrets.get("GIGACHAT_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("GigaChat Authorization Key:", value=saved_key, type="password")
    st.divider()
    st.header("📜 История генераций")
    if not st.session_state.history:
        st.caption("Здесь появятся ваши рецепты и рационы.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            icon = "📅" if item.get("mode") == "day" else "🍽️"
            if st.button(f"{icon} {item['title']}", key=f"hist_{idx}", use_container_width=True):
                st.session_state.current = item

st.title("👨‍🍳 AI-Шеф Про: Генератор рецептов и рационов")
st.caption("Умный подбор блюд и меню на день с расчетом КБЖУ, бюджета и спорт-режимом")
col1, col2 = st.columns([1, 1.3], gap="large")

with col1:
    with st.container(border=True):
        gen_mode = st.radio("Режим работы:", ["🍲 Одно блюдо", "📅 Рацион на весь день"], horizontal=True)
        st.divider()
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
        if gen_mode == "🍲 Одно блюдо":
            c1, c2 = st.columns(2)
            meal = c1.selectbox("Прием пищи:", ["Любой", "Завтрак", "Обед", "Ужин", "Перекус"])
            time_lim = c2.selectbox("Время:", ["Не важно", "До 15 мин", "До 30 мин", "До 1 часа"])
        else:
            meal, time_lim = "Весь день", "Не важно"
