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
    max-height: 360px;
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
    sport_rule = "РЕЖИМ СПОРТ-ПИТАНИЯ: сделай акцент на высоком белке и минимуме жиров. " if sport_mode else ""
    sys_prompt = (
        "Ты креативный шеф-повар. Придумай вкусное блюдо строго из переданных продуктов (можно добавить соль, перец, воду, масло, сахар). "
        f"{sport_rule}Придумывай разнообразные форматы (вок, рагу, паста, рулеты, супы, салаты, сэндвичи, стейк, лазанья) и НЕ предлагай запеканки. "
        "Оцени среднюю стоимость граммовки продуктов в рублях (РФ). Оформи ответ строго по меткам без # и *:\n"
        "TITLE: Название\nKEYWORD: 1 слово (chicken, beef, steak, pasta, salad, lasagna, fish, soup, pancake, egg, rice, potato, sandwich, dessert)\n"
        "TIME: Время\nDIFF: Сложность\nCAL: Калории на 100г\nCOST: Цена блюда (коротко, например: ~290 ₽)\nMACROS: Б: ... | Ж: ... | У: ...\n"
        "INGREDIENTS:\n- Ингредиент с граммовкой (~цена ₽)\nSTEPS:\n1. Шаг приготовления\nTIP: Совет шефа\nPAIRING: Соус, гарнир или напиток"
    )
    avoid_text = f" Не повторяй: {', '.join(past_titles)}." if past_titles else ""
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

    if not data["steps"]: data["steps"] = [text]
    data["photo"] = find_dish_photo(data["keyword"])
    return data

def fetch_day_ration(auth_key: str, ingredients: list, wishes: str, sport_mode: bool) -> dict:
    sport_rule = "Упор на высокий белок. " if sport_mode else ""
    sys_prompt = (
        "Ты диетолог. Составь рацион на день (Завтрак, Обед, Ужин) из переданных продуктов (можно добавить базовые специи, воду, масло, крупы). "
        f"{sport_rule}Посчитай примерную цену каждого приема пищи и итог за день в рублях. Оформи строго по меткам без # и *:\n"
        "TOTAL_COST: ~620 ₽\nTOTAL_CAL: ~1850 ккал\nTOTAL_MACROS: Б: ...г | Ж: ...г | У: ...г\n"
        "BREAKFAST_TITLE: Название завтрака\nBREAKFAST_KW: 1 слово на англ (egg, pancake, sandwich, salad)\nBREAKFAST_INFO: Состав, граммовка, цена и шаги\n"
        "LUNCH_TITLE: Название обеда\nLUNCH_KW: 1 слово на англ (soup, chicken, beef, pasta, rice, fish)\nLUNCH_INFO: Состав, граммовка, цена и шаги\n"
        "DINNER_TITLE: Название ужина\nDINNER_KW: 1 слово на англ (salad, fish, chicken, steak, potato, lasagna)\nDINNER_INFO: Состав, граммовка, цена и шаги\n"
        "TIP: Совет диетолога"
    )
    usr_prompt = f"Продукты: {', '.join(ingredients)}. Пожелания: {wishes or 'Сбалансированно'}."
    text = call_gigachat(auth_key, sys_prompt, usr_prompt)

    data = {
        "mode": "day", "title": "Рацион на день", "cost": "~600 ₽", "cal": "~1800 ккал",
        "macros": "Сбалансировано", "b_title": "Завтрак", "b_kw": "egg", "b_info": "",
        "l_title": "Обед", "l_kw": "soup", "l_info": "", "d_title": "Ужин", "d_kw": "chicken", "d_info": "", "tip": "", "raw": text
    }
    curr = None
    for line in text.splitlines():
        s = line.strip().lstrip("#* ").rstrip("*")
        if not s: continue
        if "TOTAL_COST:" in s: data["cost"] = s.split("TOTAL_COST:", 1).pop().strip().strip('*')
        elif "TOTAL_CAL:" in s: data["cal"] = s.split("TOTAL_CAL:", 1).pop().strip().strip('*')
        elif "TOTAL_MACROS:" in s: data["macros"] = s.split("TOTAL_MACROS:", 1).pop().strip().strip('*')
        elif "BREAKFAST_TITLE:" in s: data["b_title"] = s.split("BREAKFAST_TITLE:", 1).pop().strip().strip('"«»*'); curr = "b"
        elif "BREAKFAST_KW:" in s: data["b_kw"] = s.split("BREAKFAST_KW:", 1).pop().strip().strip('*')
        elif "BREAKFAST_INFO:" in s: data["b_info"] = s.split("BREAKFAST_INFO:", 1).pop().strip(); curr = "b"
        elif "LUNCH_TITLE:" in s: data["l_title"] = s.split("LUNCH_TITLE:", 1).pop().strip().strip('"«»*'); curr = "l"
        elif "LUNCH_KW:" in s: data["l_kw"] = s.split("LUNCH_KW:", 1).pop().strip().strip('*')
        elif "LUNCH_INFO:" in s: data["l_info"] = s.split("LUNCH_INFO:", 1).pop().strip(); curr = "l"
        elif "DINNER_TITLE:" in s: data["d_title"] = s.split("DINNER_TITLE:", 1).pop().strip().strip('"«»*'); curr = "d"
        elif "DINNER_KW:" in s: data["d_kw"] = s.split("DINNER_KW:", 1).pop().strip().strip('*')
        elif "DINNER_INFO:" in s: data["d_info"] = s.split("DINNER_INFO:", 1).pop().strip(); curr = "d"
        elif "TIP:" in s: data["tip"] = s.split("TIP:", 1).pop().strip().strip('*'); curr = None
        elif curr == "b": data["b_info"] += "\n" + s
        elif curr == "l": data["l_info"] += "\n" + s
        elif curr == "d": data["d_info"] += "\n" + s

    data["b_photo"] = find_dish_photo(data["b_kw"])
    data["l_photo"] = find_dish_photo(data["l_kw"])
    data["d_photo"] = find_dish_photo(data["d_kw"])
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
                with st.spinner("Шеф-повар рассчитывает меню и бюджет..."):
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
                with t1:
                    st.markdown(f"### {rec['b_title']}")
                    if rec.get("b_photo"): st.image(rec["b_photo"], use_container_width=True)
                    st.write(rec["b_info"] or rec["raw"])
                with t2:
                    st.markdown(f"### {rec['l_title']}")
                    if rec.get("l_photo"): st.image(rec["l_photo"], use_container_width=True)
                    st.write(rec["l_info"] or "Смотрите общий план во вкладке Завтрак.")
                with t3:
                    st.markdown(f"### {rec['d_title']}")
                    if rec.get("d_photo"): st.image(rec["d_photo"], use_container_width=True)
                    st.write(rec["d_info"] or "Смотрите общий план во вкладке Завтрак.")

                if rec.get("tip"):
                    st.success(f"💡 **Совет диетолога:** {rec['tip']}")
                txt = f"Рацион на день ({rec['cost']}, {rec['cal']})\n\nЗАВТРАК: {rec['b_title']}\n{rec['b_info']}\n\nОБЕД: {rec['l_title']}\n{rec['l_info']}\n\nУЖИН: {rec['d_title']}\n{rec['d_info']}"
                st.download_button("📥 Скачать рацион (.txt)", txt, file_name="day_ration.txt", use_container_width=True)
            else:
                st.markdown(f"## {rec['title']}")
                if rec.get("photo"):
                    st.image(rec["photo"], use_container_width=True)

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

                st.markdown("### 👨‍🍳 Приготовление:")
                for i, step in enumerate(rec["steps"], 1):
                    st.checkbox(f"**Шаг {i}.** {step}", key=f"step_{rec['title']}_{i}")

                if rec.get("tip"):
                    st.success(f"💡 **Совет шефа:** {rec['tip']}")
                if rec.get("pairing"):
                    st.info(f"🍷 **Идеальное дополнение:** {rec['pairing']}")

                txt = f"{rec['title']} ({rec.get('cost', '')})\n\nИнгредиенты:\n" + "\n".join(rec["ings"]) + "\n\nШаги:\n" + "\n".join(rec["steps"])
                st.download_button("📥 Скачать рецепт (.txt)", txt, file_name="recipe.txt", use_container_width=True)
        else:
            st.markdown("### 👋 Добро пожаловать на кухню ИИ-Шефа!")
            st.write("1. Выберите режим: **Одно блюдо** или **Рацион на весь день**.")
            st.write("2. Отметьте продукты в меню слева или впишите свои через запятую.")
            st.write("3. Нажмите кнопку генерации — нейросеть рассчитает КБЖУ, бюджет и распишет шаги.")
            st.info("💡 Все сгенерированные блюда и рационы сохраняются в левой панели.")
