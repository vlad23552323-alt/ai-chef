import streamlit as st
import requests
import uuid
import urllib3
import time
import re
import base64

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
    max-height: 440px;
    width: auto;
    max-width: 100%;
    margin: 0 auto;
    display: block;
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
BASE_GIGA = "https://" + "gigachat.devices.sberbank.ru" + "/api/v1"
API_URL = BASE_GIGA + "/chat/completions"

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
def fallback_dish_photo(keyword: str) -> str:
    m = "https://" + "www.themealdb." + "com/images/media/meals/"
    photos = {
        "fried_eggs": m + "1550441882.jpg", "omelette": m + "ryppsv1511815505.jpg",
        "pancake": m + "rwuyqx1511383174.jpg", "sandwich": m + "xr0n4r1576788363.jpg",
        "stew": m + "sytuqu1511553755.jpg", "meatloaf": m + "vtqxtu1511784197.jpg",
        "steak": m + "vussxq1511882648.jpg", "chicken": m + "wyxwsp1486979827.jpg",
        "pasta": m + "ustsqw1468250014.jpg", "lasagna": m + "wtsvxx1511296896.jpg",
        "soup": m + "1529446352.jpg", "salad": m + "wvpsxx1468256321.jpg",
        "rice": m + "xxpqsy1511452222.jpg", "potato": m + "vrspxv1511722107.jpg",
        "fish": m + "1548772327.jpg", "dessert": m + "wyrqqq1468233628.jpg"
    }
    kw = keyword.lower().strip()
    for key, url in photos.items():
        if key in kw or kw in key:
            return url
    return photos["stew"]

def generate_exact_dish_photo(auth_key: str, dish_title: str, ings: list, fallback_kw: str) -> str:
    try:
        token = get_gigachat_token(auth_key)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
        short_ings = ", ".join(ings[:4]) if ings else ""
        prompt = (
            f"Нарисуй реалистичную студийную фуд-фотографию высокого качества: {dish_title}. "
            f"Ингредиенты в тарелке: {short_ings}. Резкий фокус, высокая детализация, ресторанная подача, естественный дневной свет, без текста."
        )
        payload = {"model": "GigaChat", "messages": [{"role": "user", "content": prompt}], "function_call": "auto"}
        r = requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=45)
        if r.status_code == 200:
            content = r.json()["choices"].pop(0)["message"]["content"]
            match = re.search(r'<img\s+src="([^"]+)"', content)
            if match:
                file_id = match.group(1)
                img_resp = requests.get(f"{BASE_GIGA}/files/{file_id}/content", headers={"Authorization": f"Bearer {token}"}, verify=False, timeout=30)
                if img_resp.status_code == 200 and img_resp.content:
                    b64 = base64.b64encode(img_resp.content).decode("utf-8")
                    return f"data:image/jpeg;base64,{b64}"
    except Exception:
        pass
    return fallback_dish_photo(fallback_kw)

def call_gigachat(auth_key: str, sys_prompt: str, usr_prompt: str) -> str:
    token = get_gigachat_token(auth_key)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": usr_prompt}],
        "temperature": 0.85
    }
    for attempt in range(4):
        r = requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=40)
        if r.status_code == 429:
            time.sleep(1.5 + attempt)
            continue
        if not r.text.strip():
            raise ValueError(f"GigaChat вернул пустой ответ (HTTP {r.status_code}). Попробуйте нажать кнопку еще раз.")
        r.raise_for_status()
        return r.json()["choices"].pop(0)["message"]["content"]
    raise ValueError("Сервер GigaChat сейчас перегружен одновременными запросами. Попробуйте через пару секунд.")
def calc_total_rub(lines: list, fallback_str: str) -> str:
    prices = [int(p) for line in lines for p in re.findall(r'(\d+)\s*(?:₽|руб)', line)]
    return f"~{sum(prices)} ₽" if prices else fallback_str

def fetch_single_recipe(auth_key: str, ingredients: list, meal: str, time_lim: str, wishes: str, sport_mode: bool, past_titles: list) -> dict:
    sport_rule = "РЕЖИМ СПОРТ-ПИТАНИЯ: сделай акцент на высоком белке и минимуме жиров. " if sport_mode else ""
    sys_prompt = (
        "Ты креативный российский шеф-повар. Пиши СТРОГО на русском языке. Придумай вкусное блюдо из переданных продуктов (можно добавить воду и масло). "
        f"{sport_rule}Придумывай разнообразные форматы (вок, рагу, паста, рулеты, супы, салаты, сэндвичи, стейк, лазанья, яичница, омлет) и НЕ предлагай запеканки. "
        "Оцени среднюю стоимость граммовки каждого продукта в рублях (РФ). "
        "Оформи ответ строго с новой строки для каждой метки, не пиши лишних слов перед метками:\n"
        "TITLE: Название блюда на русском\n"
        "KEYWORD: 1 слово (fried_eggs, omelette, pancake, sandwich, stew, meatloaf, steak, chicken, pasta, lasagna, soup, salad, rice, potato, fish, dessert)\n"
        "TIME: Время\nDIFF: Сложность\nCAL: Калории на 100г\nCOST: ~290 ₽\nMACROS: Б: ... | Ж: ... | У: ...\n"
        "SPICES: 3-4 конкретные специи и пряности, которые идеально подходят именно к этому блюду (только названия через запятую)\n"
        "INGREDIENTS:\n- Ингредиент (граммовка, цена ₽)\n"
        "STEPS:\n1. Первый шаг приготовления\n2. Второй шаг приготовления\n"
        "TIP: Короткий совет шефа\nPAIRING: Идеальный соус, гарнир или напиток"
    )
    avoid_text = f" Не повторяй: {', '.join(past_titles)}." if past_titles else ""
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Прием пищи: {meal}. Время: {time_lim}. Пожелания: {wishes or 'Нет'}.{avoid_text}"
    text = call_gigachat(auth_key, sys_prompt, usr_prompt)

    data = {
        "mode": "single", "title": "Блюдо от шефа", "keyword": "stew", "time": time_lim,
        "diff": "Средне", "cal": "Не указано", "cost": "~250 ₽", "macros": "Сбалансировано",
        "spices": "Соль, свежемолотый черный перец", "ings": [], "steps": [], "tip": "", "pairing": "", "photo": ""
    }
    mode = None
    for line in text.splitlines():
        s = re.sub(r'^(МЕТА\d*:|META\d*:|\s|[#*])+', '', line).strip().rstrip("*")
        if not s: continue
        upper_s = s.upper()
        if "TITLE:" in upper_s: data["title"] = s.split(":", 1).pop().strip().strip('"«»*')
        elif "KEYWORD:" in upper_s: data["keyword"] = s.split(":", 1).pop().strip().strip('*')
        elif "TIME:" in upper_s: data["time"] = s.split(":", 1).pop().strip().strip('*')
        elif "DIFF:" in upper_s: data["diff"] = s.split(":", 1).pop().strip().strip('*')
        elif "CAL:" in upper_s: data["cal"] = s.split(":", 1).pop().strip().strip('*')
        elif "COST:" in upper_s: data["cost"] = s.split(":", 1).pop().strip().strip('*')
        elif "MACROS:" in upper_s: data["macros"] = s.split(":", 1).pop().strip().strip('*')
        elif "SPICES:" in upper_s: data["spices"] = s.split(":", 1).pop().strip().strip('*')
        elif "TIP:" in upper_s: data["tip"] = s.split(":", 1).pop().strip().strip('*'); mode = None
        elif "PAIRING:" in upper_s: data["pairing"] = s.split(":", 1).pop().strip().strip('*'); mode = None
        elif upper_s.startswith("INGREDIENTS"): mode = "ing"
        elif upper_s.startswith("STEPS"): mode = "step"
        elif mode == "ing":
            if re.match(r'^1[\.\)]', s):
                mode = "step"
                data["steps"].append(re.sub(r'^\d+[\.\)]\s*', '', s))
            else:
                data["ings"].append(s.lstrip("-•* ").strip())
        elif mode == "step":
            data["steps"].append(re.sub(r'^\d+[\.\)]\s*', '', s))

    data["cost"] = calc_total_rub(data["ings"], data["cost"])
    data["photo"] = generate_exact_dish_photo(auth_key, data["title"], data["ings"], data["keyword"])
    return data

def fetch_day_ration(auth_key: str, ingredients: list, wishes: str, sport_mode: bool) -> dict:
    sport_rule = "Упор на высокий белок. " if sport_mode else ""
    sys_prompt = (
        "Ты российский диетолог. Пиши все названия блюд, ингредиенты и шаги СТРОГО НА РУССКОМ ЯЗЫКЕ! "
        "Составь рацион на день (Завтрак, Обед, Ужин) из переданных продуктов (можно добавить воду, масло, крупы). "
        f"{sport_rule}Укажи примерную цену каждого ингредиента в рублях. "
        "Оформляй каждый ингредиент и шаг С НОВОЙ СТРОКИ! Строго по меткам без # и *:\n"
        "TOTAL_COST: ~620 ₽\nTOTAL_CAL: ~1850 ккал\nTOTAL_MACROS: Б: ...г | Ж: ...г | У: ...г\n"
        "BREAKFAST_TITLE: Название завтрака НА РУССКОМ\nBREAKFAST_KW: fried_eggs\n"
        "BREAKFAST_INGS:\n- Продукт 1 (граммовка, цена ₽)\n- Продукт 2 (граммовка, цена ₽)\n"
        "BREAKFAST_STEPS:\n1. Первый шаг\n2. Второй шаг\n"
        "LUNCH_TITLE: Название обеда НА РУССКОМ\nLUNCH_KW: soup\n"
        "LUNCH_INGS:\n- Продукт 1 (граммовка, цена ₽)\n- Продукт 2 (граммовка, цена ₽)\n"
        "LUNCH_STEPS:\n1. Первый шаг\n2. Второй шаг\n"
        "DINNER_TITLE: Название ужина НА РУССКОМ\nDINNER_KW: chicken\n"
        "DINNER_INGS:\n- Продукт 1 (граммовка, цена ₽)\n- Продукт 2 (граммовка, цена ₽)\n"
        "DINNER_STEPS:\n1. Первый шаг\n2. Второй шаг\n"
        "TIP: Совет диетолога на русском"
    )
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Пожелания: {wishes or 'Сбалансированно'}."
    text = call_gigachat(auth_key, sys_prompt, usr_prompt)

    data = {
        "mode": "day", "title": "Рацион на день", "cost": "~600 ₽", "cal": "~1800 ккал", "macros": "Сбалансировано",
        "b_title": "Завтрак", "b_kw": "fried_eggs", "b_ings": [], "b_steps": [],
        "l_title": "Обед", "l_kw": "soup", "l_ings": [], "l_steps": [],
        "d_title": "Ужин", "d_kw": "chicken", "d_ings": [], "d_steps": [], "tip": "", "raw": text
    }
    curr = None
    for line in text.splitlines():
        s = re.sub(r'^(МЕТА\d*:|META\d*:|\s|[#*])+', '', line).strip().rstrip("*")
        if not s: continue
        upper_s = s.upper()
        if "TOTAL_COST:" in upper_s: data["cost"] = s.split(":", 1).pop().strip().strip('*')
        elif "TOTAL_CAL:" in upper_s: data["cal"] = s.split(":", 1).pop().strip().strip('*')
        elif "TOTAL_MACROS:" in upper_s: data["macros"] = s.split(":", 1).pop().strip().strip('*')
        elif "BREAKFAST_TITLE:" in upper_s: data["b_title"] = s.split(":", 1).pop().strip().strip('"«»*')
        elif "BREAKFAST_KW:" in upper_s: data["b_kw"] = s.split(":", 1).pop().strip().strip('*')
        elif upper_s.startswith("BREAKFAST_INGS"): curr = "b_ing"
        elif upper_s.startswith("BREAKFAST_STEPS"): curr = "b_step"
        elif "LUNCH_TITLE:" in upper_s: data["l_title"] = s.split(":", 1).pop().strip().strip('"«»*')
        elif "LUNCH_KW:" in upper_s: data["l_kw"] = s.split(":", 1).pop().strip().strip('*')
        elif upper_s.startswith("LUNCH_INGS"): curr = "l_ing"
        elif upper_s.startswith("LUNCH_STEPS"): curr = "l_step"
        elif "DINNER_TITLE:" in upper_s: data["d_title"] = s.split(":", 1).pop().strip().strip('"«»*')
        elif "DINNER_KW:" in upper_s: data["d_kw"] = s.split(":", 1).pop().strip().strip('*')
        elif upper_s.startswith("DINNER_INGS"): curr = "d_ing"
        elif upper_s.startswith("DINNER_STEPS"): curr = "d_step"
        elif "TIP:" in upper_s: data["tip"] = s.split(":", 1).pop().strip().strip('*'); curr = None
        elif curr == "b_ing": data["b_ings"].append(s.lstrip("-•* ").strip())
        elif curr == "b_step": data["b_steps"].append(re.sub(r'^\d+[\.\)]\s*', '', s))
        elif curr == "l_ing": data["l_ings"].append(s.lstrip("-•* ").strip())
        elif curr == "l_step": data["l_steps"].append(re.sub(r'^\d+[\.\)]\s*', '', s))
        elif curr == "d_ing": data["d_ings"].append(s.lstrip("-•* ").strip())
        elif curr == "d_step": data["d_steps"].append(re.sub(r'^\d+[\.\)]\s*', '', s))

    all_day_ings = data["b_ings"] + data["l_ings"] + data["d_ings"]
    data["cost"] = calc_total_rub(all_day_ings, data["cost"])
    data["b_photo"] = fallback_dish_photo(data["b_kw"])
    data["l_photo"] = fallback_dish_photo(data["l_kw"])
    data["d_photo"] = fallback_dish_photo(data["d_kw"])
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
            st.caption("ИИ-диетолог распределит выбранные продукты на Завтрак, Обед и Ужин.")

        sport_mode = st.toggle("💪 Спортивное / Белковое меню (высокий белок)")
        wishes = st.text_input("✨ Пожелания (бюджет до 600р, ПП, без жарки):")
        btn_label = "🔥 Придумать рецепт" if gen_mode == "🍲 Одно блюдо" else "📅 Составить рацион на день"
        btn = st.button(btn_label, type="primary", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("🍽️ Результат от шефа")
        regen = False
        if "current" in st.session_state and st.session_state.current.get("mode") == "single":
            regen = st.button("🔄 Другой вариант из этих же продуктов", use_container_width=True)

        if btn or regen:
            if not api_key:
                st.error("⚠️ Введите Authorization Key в меню слева!")
            elif not selected:
                st.error("⚠️ Выберите хотя бы один продукт!")
            else:
                with st.spinner("Шеф-повар готовит рецепт и создает фото блюда..."):
                    try:
                        if gen_mode == "🍲 Одно блюдо" or regen:
                            past = [item["title"] for item in st.session_state.history if item.get("mode") == "single"]
                            res = fetch_single_recipe(api_key, selected, meal, time_lim, wishes, sport_mode, past)
                        else:
                            res = fetch_day_ration(api_key, selected, wishes, sport_mode)
                        st.session_state.history.append(res)
                        st.session_state.current = res
                        st.rerun()
                    except Exception as e:
                        st.error(f"🚨 Ошибка: {e}")

        if "current" in st.session_state:
            rec = st.session_state.current
            if rec.get("mode") == "day":
                st.markdown("## 📅 Сбалансированный рацион на день")
                m1, m2, m3 = st.columns(3)
                m1.metric("💰 Бюджет за день", rec["cost"])
                m2.metric("🔥 Калории за день", rec["cal"])
                m3.metric("📊 Приемов пищи", "3 (З / О / У)")
                st.caption(f"**Общее БЖУ за день:** {rec['macros']}")
                st.divider()

                t1, t2, t3 = st.tabs(["🌅 Завтрак", "☀️ Обед", "🌙 Ужин"])
                meals_data = [
                    (t1, rec["b_title"], rec.get("b_photo"), rec.get("b_ings", []), rec.get("b_steps", [])),
                    (t2, rec["l_title"], rec.get("l_photo"), rec.get("l_ings", []), rec.get("l_steps", [])),
                    (t3, rec["d_title"], rec.get("d_photo"), rec.get("d_ings", []), rec.get("d_steps", []))
                ]
                for tab, m_title, m_photo, m_ings, m_steps in meals_data:
                    with tab:
                        st.markdown(f"### {m_title}")
                        if m_photo: st.image(m_photo)
                        if m_ings:
                            st.markdown("**🛒 Ингредиенты:**")
                            for ing in m_ings: st.markdown(f"- {ing}")
                        if m_steps:
                            st.markdown("**👨‍🍳 Приготовление:**")
                            for idx, step in enumerate(m_steps, 1): st.markdown(f"**{idx}.** {step}")
                        if not m_ings and not m_steps:
                            st.write(rec["raw"])

                if rec.get("tip"):
                    st.success(f"💡 **Совет диетолога:** {rec['tip']}")
                txt = f"Рацион на день ({rec['cost']}, {rec['cal']})\n\nЗАВТРАК: {rec['b_title']}\n" + "\n".join(rec.get("b_steps", []))
                st.download_button("📥 Скачать рацион (.txt)", txt, file_name="day_ration.txt", use_container_width=True)
            else:
                st.markdown(f"## {rec['title']}")
                if rec.get("photo"):
                    st.image(rec["photo"])

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("⏱️ Время", rec["time"])
                m2.metric("📊 Сложность", rec["diff"])
                m3.metric("🔥 Калории", rec["cal"])
                m4.metric("💰 Бюджет", rec.get("cost", "~250 ₽"))
                st.caption(f"**БЖУ:** {rec['macros']}")
                st.divider()

                st.markdown("### 🛒 Ингредиенты (с примерной ценой):")
                for i, ing in enumerate(rec["ings"]):
                    st.checkbox(ing, key=f"ing_{rec['title']}_{i}")

                if rec.get("spices"):
                    st.warning(f"🧂 **Подходящие специи:** {rec['spices']}")

                st.markdown("### 👨‍🍳 Приготовление:")
                for i, step in enumerate(rec["steps"], 1):
                    st.checkbox(f"**Шаг {i}.** {step}", key=f"step_{rec['title']}_{i}")

                if rec.get("tip"):
                    st.success(f"💡 **Совет шефа:** {rec['tip']}")
                if rec.get("pairing"):
                    st.info(f"🍷 **Идеальное дополнение:** {rec['pairing']}")

                txt = f"{rec['title']} ({rec.get('cost', '')})\n\nСпеции: {rec.get('spices', '')}\n\nИнгредиенты:\n" + "\n".join(rec["ings"]) + "\n\nШаги:\n" + "\n".join(rec["steps"])
                st.download_button("📥 Скачать рецепт (.txt)", txt, file_name="recipe.txt", use_container_width=True)
        else:
            st.markdown("### 👋 Добро пожаловать на кухню ИИ-Шефа!")
            st.write("1. Выберите режим: **Одно блюдо** или **Рацион на весь день**.")
            st.write("2. Отметьте продукты в меню слева или впишите свои через запятую.")
            st.write("3. Нажмите кнопку генерации — нейросеть рассчитает КБЖУ, бюджет, подберет специи и создаст фото.")
            st.info("💡 Все сгенерированные блюда и рационы сохраняются в левой панели.")
