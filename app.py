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
if "ideas" not in st.session_state:
    st.session_state.ideas = []

@st.cache_resource
def get_http_session():
    s = requests.Session()
    s.verify = False
    return s

@st.cache_data(ttl=1500, show_spinner=False)
def get_gigachat_token(auth_key: str) -> str:
    sess = get_http_session()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_key.strip()}"
    }
    for attempt in range(3):
        try:
            r = sess.post(AUTH_URL, headers=headers, data={"scope": "GIGACHAT_API_PERS"}, timeout=15)
            if r.status_code == 200 and r.text.strip():
                return r.json()["access_token"]
        except requests.exceptions.RequestException:
            time.sleep(0.8)
    raise ValueError("Ошибка авторизации Сбера. Проверьте ключ и интернет-соединение.")
@st.cache_data(ttl=86400, show_spinner=False)
def fallback_dish_photo(keyword: str, title_ru: str = "") -> str:
    sess = get_http_session()
    m = "https://" + "www.themealdb." + "com/images/media/meals/"
    api_base = "https://" + "www.themealdb." + "com/api/json/v1/1/"

    photos = {
        "omelette": m + "g373701551450225.jpg",
        "shakshuka": m + "g373701551450225.jpg",
        "fried_eggs": m + "1550441882.jpg",
        "eggs": m + "1550441882.jpg",
        "kebab": m + "tyywsw1505930373.jpg", "shashlik": m + "tyywsw1505930373.jpg",
        "porridge": m + "1549542992.jpg", "oatmeal": m + "1549542992.jpg",
        "pancake": m + "rwuyqx1511383174.jpg", "cheesecake": m + "rwuyqx1511383174.jpg",
        "sandwich": m + "xr0n4r1576788363.jpg", "toast": m + "xr0n4r1576788363.jpg",
        "shawarma": m + "k29viq1585565980.jpg", "wrap": m + "k29viq1585565980.jpg", "roll": m + "k29viq1585565980.jpg",
        "burger": m + "k420tj1585565244.jpg", "pizza": m + "x0lk931587671540.jpg",
        "pie": m + "wrssvt1511556563.jpg", "casserole": m + "wtsvxx1511296896.jpg", "lasagna": m + "wtsvxx1511296896.jpg",
        "dumplings": m + "1525876468.jpg", "pelmeni": m + "1525876468.jpg",
        "stew": m + "sytuqu1511553755.jpg", "ragout": m + "sytuqu1511553755.jpg", "goulash": m + "sytuqu1511553755.jpg",
        "meatloaf": m + "vtqxtu1511784197.jpg", "cutlet": m + "vtqxtu1511784197.jpg", "meatballs": m + "vtqxtu1511784197.jpg",
        "steak": m + "vussxq1511882648.jpg", "beef": m + "vussxq1511882648.jpg", "pork": m + "vussxq1511882648.jpg",
        "chicken": m + "wyxwsp1486979827.jpg", "turkey": m + "wyxwsp1486979827.jpg",
        "pasta": m + "ustsqw1468250014.jpg", "spaghetti": m + "ustsqw1468250014.jpg", "macaroni": m + "ustsqw1468250014.jpg",
        "noodles": m + "1529446137.jpg", "wok": m + "1529446137.jpg",
        "soup": m + "1529446352.jpg", "borscht": m + "1529446352.jpg",
        "salad": m + "wvpsxx1468256321.jpg", "rice": m + "xxpqsy1511452222.jpg", "pilaf": m + "xxpqsy1511452222.jpg",
        "buckwheat": m + "xxpqsy1511452222.jpg", "potato": m + "vrspxv1511722107.jpg",
        "fish": m + "1548772327.jpg", "salmon": m + "1548772327.jpg", "tuna": m + "1548772327.jpg",
        "shrimp": m + "1529445834.jpg", "seafood": m + "1529445834.jpg",
        "dessert": m + "wyrqqq1468233628.jpg", "cake": m + "wyrqqq1468233628.jpg"
    }

    t_low = title_ru.lower()
    ru_map = {
        "омлет": "omelette", "шакшук": "omelette", "яичн": "fried_eggs", "глазун": "fried_eggs",
        "шашлык": "kebab", "кебаб": "kebab", "суп": "soup", "борщ": "soup", "щи": "soup",
        "паст": "pasta", "макарон": "pasta", "спагетти": "pasta", "вок": "wok", "лапш": "wok",
        "салат": "salad", "плов": "pilaf", "ризотто": "pilaf", "гречк": "buckwheat",
        "котлет": "cutlet", "тефтел": "cutlet", "рулет": "meatloaf", "стейк": "steak",
        "каша": "porridge", "овсян": "porridge", "блин": "pancake", "сырник": "pancake",
        "шаурм": "shawarma", "лаваш": "shawarma", "сэндвич": "sandwich", "бутерброд": "sandwich",
        "пельмен": "dumplings", "вареник": "dumplings", "рыб": "fish", "лосос": "fish", "тунец": "fish"
    }
    for ru_stem, mapped_kw in ru_map.items():
        if ru_stem in t_low:
            return photos[mapped_kw]

    kw = keyword.lower().strip().replace(" ", "_")
    if kw in photos:
        return photos[kw]
    for key, url in photos.items():
        if key in kw or kw in key:
            return url

    clean_word = kw.replace("_", " ")
    for endpoint in [f"search.php?s={clean_word}", f"filter.php?i={clean_word}"]:
        try:
            resp = sess.get(api_base + endpoint, timeout=3).json()
            if resp.get("meals"):
                return resp["meals"].pop(0)["strMealThumb"]
        except Exception:
            pass

    return photos["stew"]
def get_dish_image(auth_key: str, dish_title: str, ings: list, fallback_kw: str, use_ai: bool) -> str:
    if use_ai:
        try:
            sess = get_http_session()
            token = get_gigachat_token(auth_key)
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
            short_ings = ", ".join(ings[:4]) if ings else ""
            prompt = f"Студийная фуд-фотография высокого качества: {dish_title}. Состав: {short_ings}. Резкий фокус, ресторанная подача, без текста."
            payload = {"model": "GigaChat", "messages": [{"role": "user", "content": prompt}], "function_call": "auto"}
            r = sess.post(API_URL, headers=headers, json=payload, timeout=35)
            if r.status_code == 200:
                content = r.json()["choices"].pop(0)["message"]["content"]
                match = re.search(r'<img\s+src="([^"]+)"', content)
                if match:
                    file_id = match.group(1)
                    img_resp = sess.get(f"{BASE_GIGA}/files/{file_id}/content", headers={"Authorization": f"Bearer {token}"}, timeout=20)
                    if img_resp.status_code == 200 and img_resp.content:
                        b64 = base64.b64encode(img_resp.content).decode("utf-8")
                        return f"data:image/jpeg;base64,{b64}"
        except Exception:
            pass
    return fallback_dish_photo(fallback_kw, dish_title)

PROD_DB = {
    "кури": (115, 38), "филе": (115, 42), "говядин": (187, 72), "свинин": (259, 45),
    "фарш": (240, 46), "рыб": (140, 58), "тунец": (130, 65), "сосиск": (260, 44),
    "яйц": (155, 22), "картоф": (77, 6), "лук": (41, 5), "морков": (35, 6),
    "помидор": (20, 22), "томат": (20, 22), "огурц": (15, 18), "чеснок": (149, 30),
    "шампиньон": (27, 32), "гриб": (27, 32), "капуст": (28, 5), "перец": (27, 25),
    "молок": (58, 9), "сыр": (350, 85), "сметан": (200, 32), "масло сливоч": (748, 110),
    "масло растит": (899, 16), "масло": (820, 25), "творог": (121, 42), "сливк": (205, 38),
    "рис": (344, 14), "макарон": (340, 13), "гречк": (313, 12), "овсян": (342, 10),
    "мук": (334, 7), "хлеб": (245, 14), "лаваш": (236, 22), "бекон": (468, 85), "ветчин": (220, 65)
}

def recalculate_nutrition_and_cost(ings: list, fallback_cal: str, fallback_cost: str):
    total_grams = 0
    total_kcal = 0.0
    total_rub = 0.0
    updated_ings = []

    for line in ings:
        low = line.lower()
        g_match = re.search(r'(\d+)\s*(?:г|гр|мл)\b', low)
        kg_match = re.search(r'(\d+(?:[.,]\d+)?)\s*кг\b', low)
        pcs_match = re.search(r'(\d+)\s*(?:шт|зубч)', low)

        grams = 0
        if g_match:
            grams = int(g_match.group(1))
        elif kg_match:
            grams = int(float(kg_match.group(1).replace(",", ".")) * 1000)
        elif pcs_match:
            cnt = int(pcs_match.group(1))
            grams = cnt * (5 if "чеснок" in low or "зубч" in low else (55 if "яйц" in low else 100))

        kcal_100, rub_100 = None, None
        for key, (k_val, r_val) in PROD_DB.items():
            if key in low:
                kcal_100, rub_100 = k_val, r_val
                break

        if grams > 0 and kcal_100 is not None:
            item_kcal = (grams / 100.0) * kcal_100
            item_rub = max(3, round((grams / 100.0) * rub_100))
            total_grams += grams
            total_kcal += item_kcal
            total_rub += item_rub
            clean_name = re.sub(r'\s*\([^)]*(?:₽|руб)[^)]*\)', '', line).strip()
            updated_ings.append(f"{clean_name} (~{item_rub} ₽)")
        else:
            p_match = re.findall(r'(\d+)\s*(?:₽|руб)', low)
            if p_match:
                total_rub += int(p_match.pop(0))
            if grams > 0:
                total_grams += grams
                total_kcal += (grams / 100.0) * 120
            updated_ings.append(line)

    final_cost = f"~{int(round(total_rub))} ₽" if total_rub > 0 else fallback_cost
    if total_grams > 0 and total_kcal > 0:
        avg_kcal = int(round((total_kcal / total_grams) * 100))
        final_cal = f"{avg_kcal} ккал"
    else:
        final_cal = fallback_cal

    return updated_ings, final_cal, final_cost
def call_gigachat(auth_key: str, sys_prompt: str, usr_prompt: str, max_tok: int = 1100) -> str:
    sess = get_http_session()
    token = get_gigachat_token(auth_key)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": usr_prompt}],
        "temperature": 0.85,
        "max_tokens": max_tok
    }
    for attempt in range(4):
        try:
            r = sess.post(API_URL, headers=headers, json=payload, timeout=30)
            if r.status_code == 429:
                time.sleep(1.2 + attempt)
                continue
            if not r.text.strip():
                time.sleep(0.8)
                continue
            r.raise_for_status()
            return r.json()["choices"].pop(0)["message"]["content"]
        except requests.exceptions.RequestException:
            if attempt == 3:
                raise ValueError("Сетевой сбой при связи с GigaChat. Нажмите кнопку еще раз.")
            time.sleep(1.0)
    raise ValueError("Сервер GigaChat сейчас перегружен. Попробуйте через пару секунд.")

def fetch_recipe_ideas(auth_key: str, ingredients: list, meal: str, time_lim: str, wishes: str, sport_mode: bool, past_titles: list) -> list:
    sport_rule = "Упор на высокий белок и минимум жиров. " if sport_mode else ""
    sys_prompt = (
        "Ты опытный шеф-повар. Тебе передан список доступных продуктов. "
        "ВАЖНОЕ ПРАВИЛО: НЕ нужно использовать все продукты сразу! Выбери для каждого блюда только 3-5 гармонично сочетающихся ингредиентов (не смешивай несовместимое вроде рыбы, сосисок и творога). "
        f"{sport_rule}Придумай 3 РАЗНЫХ варианта блюд (разные форматы: суп, паста, салат, жаркое, шашлык, рулет, вок, омлет и т.д.). "
        "Оформи ответ строго по 3 строкам без лишнего текста:\n"
        "IDEA: Название блюда 1 | Время | Калории на 100г | Примерная цена ₽ | Краткое описание (из каких 3-5 продуктов готовится)\n"
        "IDEA: Название блюда 2 | Время | Калории на 100г | Примерная цена ₽ | Краткое описание\n"
        "IDEA: Название блюда 3 | Время | Калории на 100г | Примерная цена ₽ | Краткое описание"
    )
    avoid_text = f" Исключи блюда: {', '.join(past_titles)}." if past_titles else ""
    usr_prompt = f"Доступные продукты: {', '.join(ingredients)}. Прием пищи: {meal}. Время: {time_lim}. Пожелания: {wishes or 'Нет'}.{avoid_text}"
    text = call_gigachat(auth_key, sys_prompt, usr_prompt, max_tok=450)
    ideas = []
    for line in text.splitlines():
        s = re.sub(r'^(МЕТА\d*:|META\d*:|\s|[#*])+', '', line).strip()
        if "IDEA:" in s.upper():
            raw = s.split(":", 1).pop().strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) >= 2:
                ideas.append({
                    "title": parts,
                    "time": parts if len(parts) > 1 else time_lim,
                    "cal": parts if len(parts) > 2 else "180 ккал",
                    "cost": parts if len(parts) > 3 else "~220 ₽",
                    "desc": parts if len(parts) > 4 else ""
                })
    return ideas[:3]
def fetch_single_recipe(auth_key: str, ingredients: list, meal: str, time_lim: str, wishes: str, sport_mode: bool, ai_photo: bool, chosen_title: str = "") -> dict:
    sport_rule = "РЕЖИМ СПОРТ-ПИТАНИЯ: высокий белок, минимум жиров. " if sport_mode else ""
    dish_focus = f"Приготовь именно это блюдо: «{chosen_title}». " if chosen_title else "Придумай вкусное блюдо. "
    sys_prompt = (
        f"Ты российский шеф-повар. Пиши СТРОГО на русском языке. {dish_focus}"
        "ВАЖНО: возьми из списка доступных продуктов ТОЛЬКО те 3-6 ингредиентов, которые реально подходят для этого рецепта (игнорируй остальные несочетаемые продукты, можно добавить воду и масло). "
        f"{sport_rule}Распиши способ приготовления МАКСИМАЛЬНО ПОДРОБНО: указывай температуру, время в минутах, нарезку и консистенцию. "
        "ОБЯЗАТЕЛЬНО указывай точную граммовку каждого ингредиента в граммах или штуках! Строго с новой строки по меткам без # и *:\n"
        "TITLE: Название блюда\n"
        "KEYWORD: 1 английское слово (kebab, fried_eggs, omelette, porridge, pancake, sandwich, shawarma, burger, pizza, pie, stew, meatloaf, cutlet, steak, chicken, pasta, lasagna, soup, salad, rice, potato, fish, shrimp, dessert)\n"
        "TIME: Время\nDIFF: Сложность\nCAL: 180 ккал\nCOST: ~220 ₽\nMACROS: Б: ... | Ж: ... | У: ...\n"
        "SPICES: 3-4 подходящие специи через запятую\n"
        "INGREDIENTS:\n- Ингредиент — 200 г\n"
        "STEPS:\n1. Подробный шаг 1\n2. Подробный шаг 2\n"
        "TIP: Полезный кулинарный секрет шефа\nPAIRING: Соус, гарнир или напиток"
    )
    usr_prompt = f"Доступные продукты: {', '.join(ingredients)}. Прием пищи: {meal}. Время: {time_lim}. Пожелания: {wishes or 'Нет'}."
    text = call_gigachat(auth_key, sys_prompt, usr_prompt, max_tok=1100)

    data = {
        "mode": "single", "title": chosen_title or "Блюдо от шефа", "keyword": "stew", "time": time_lim,
        "diff": "Средне", "cal": "180 ккал", "cost": "~220 ₽", "macros": "Сбалансировано",
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

    data["ings"], data["cal"], data["cost"] = recalculate_nutrition_and_cost(data["ings"], data["cal"], data["cost"])
    data["photo"] = get_dish_image(auth_key, data["title"], data["ings"], data["keyword"], ai_photo)
    return data

def fetch_day_ration(auth_key: str, ingredients: list, wishes: str, sport_mode: bool, ai_photo: bool) -> dict:
    sport_rule = "Упор на высокий белок. " if sport_mode else ""
    sys_prompt = (
        "Ты российский диетолог. Пиши СТРОГО НА РУССКОМ языке! "
        "Составь сбалансированный рацион на день (Завтрак, Обед, Ужин) из переданных продуктов (для каждого приема пищи выбирай только сочетаемые продукты; обязательно указывай граммовку в граммах или штуках). "
        f"{sport_rule}Распиши шаги подробно с временем и температурой. Каждый пункт С НОВОЙ СТРОКИ по меткам без # и *:\n"
        "TOTAL_COST: ~620 ₽\nTOTAL_CAL: ~1850 ккал\nTOTAL_MACROS: Б: ...г | Ж: ...г | У: ...г\n"
        "BREAKFAST_TITLE: Название завтрака\nBREAKFAST_KW: omelette\n"
        "BREAKFAST_INGS:\n- Продукт 1 — 150 г\n"
        "BREAKFAST_STEPS:\n1. Подробный шаг\n"
        "LUNCH_TITLE: Название обеда\nLUNCH_KW: soup\n"
        "LUNCH_INGS:\n- Продукт 1 — 200 г\n"
        "LUNCH_STEPS:\n1. Подробный шаг\n"
        "DINNER_TITLE: Название ужина\nDINNER_KW: chicken\n"
        "DINNER_INGS:\n- Продукт 1 — 200 г\n"
        "DINNER_STEPS:\n1. Подробный шаг\n"
        "TIP: Подробный совет диетолога"
    )
    usr_prompt = f"Доступные продукты: {', '.join(ingredients)}. Пожелания: {wishes or 'Сбалансированно'}."
    text = call_gigachat(auth_key, sys_prompt, usr_prompt, max_tok=1200)

    data = {
        "mode": "day", "title": "Рацион на день", "cost": "~600 ₽", "cal": "~1800 ккал", "macros": "Сбалансировано",
        "b_title": "Завтрак", "b_kw": "omelette", "b_ings": [], "b_steps": [],
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

    data["b_ings"], _, b_cost = recalculate_nutrition_and_cost(data["b_ings"], "", "~150 ₽")
    data["l_ings"], _, l_cost = recalculate_nutrition_and_cost(data["l_ings"], "", "~250 ₽")
    data["d_ings"], _, d_cost = recalculate_nutrition_and_cost(data["d_ings"], "", "~200 ₽")
    day_sum = sum(int(re.sub(r'\D', '', c) or 0) for c in [b_cost, l_cost, d_cost])
    if day_sum > 0:
        data["cost"] = f"~{day_sum} ₽"

    data["b_photo"] = get_dish_image(auth_key, data["b_title"], data["b_ings"], data["b_kw"], ai_photo)
    data["l_photo"] = get_dish_image(auth_key, data["l_title"], data["l_ings"], data["l_kw"], ai_photo)
    data["d_photo"] = get_dish_image(auth_key, data["d_title"], data["d_ings"], data["d_kw"], ai_photo)
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
st.caption("Точный расчёт калорий и стоимости граммовки, выбор из 3 блюд и подробные шаги")
col1, col2 = st.columns([1, 1.3], gap="large")

with col1:
    with st.container(border=True):
        gen_mode = st.radio("Режим работы:", ["🍲 Варианты блюд (3 на выбор)", "📅 Рацион на весь день"], horizontal=True)
        st.divider()
        st.subheader("1. Продукты в наличии")
        st.caption("Можно отметить хоть всё — шеф сам выберет 3–5 сочетаемых продуктов для каждого блюда.")
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
        if "Варианты" in gen_mode:
            c1, c2 = st.columns(2)
            meal = c1.selectbox("Прием пищи:", ["Любой", "Завтрак", "Обед", "Ужин", "Перекус"])
            time_lim = c2.selectbox("Время:", ["Не важно", "До 15 мин", "До 30 мин", "До 1 часа"])
        else:
            meal, time_lim = "Весь день", "Не важно"
            st.caption("ИИ-диетолог распределит сочетаемые продукты на Завтрак, Обед и Ужин.")

        sport_mode = st.toggle("💪 Спортивное / Белковое меню (высокий белок)")
        ai_photo = st.toggle("🎨 Рисовать уникальные фото нейросетью (+10 сек)", value=False)
        wishes = st.text_input("✨ Пожелания (бюджет до 600р, ПП, без жарки):")
        btn_label = "🔥 Подобрать 3 блюда на выбор" if "Варианты" in gen_mode else "📅 Составить рацион на день"
        btn = st.button(btn_label, type="primary", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("🍽️ Результат от шефа")

        if btn:
            if not api_key:
                st.error("⚠️ Введите Authorization Key в меню слева!")
            elif not selected:
                st.error("⚠️ Выберите хотя бы один продукт!")
            else:
                with st.spinner("Шеф-повар подбирает сочетания и рассчитывает КБЖУ..."):
                    try:
                        if "Варианты" in gen_mode:
                            past = [item["title"] for item in st.session_state.history if item.get("mode") == "single"]
                            st.session_state.ideas = fetch_recipe_ideas(api_key, selected, meal, time_lim, wishes, sport_mode, past)
                        else:
                            res = fetch_day_ration(api_key, selected, wishes, sport_mode, ai_photo)
                            st.session_state.history.append(res)
                            st.session_state.current = res
                            st.session_state.ideas = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"🚨 Ошибка: {e}")

        if st.session_state.ideas:
            st.markdown("### 🎯 Выберите одно из 3 предложенных блюд:")
            for idx, idea in enumerate(st.session_state.ideas):
                with st.container(border=True):
                    c_info, c_btn = st.columns([3, 1.2])
                    c_info.markdown(f"**{idx+1}. {idea['title']}**")
                    c_info.caption(f"⏱️ {idea['time']} | 🔥 {idea['cal']} | 💰 {idea['cost']} — {idea['desc']}")
                    if c_btn.button("👨‍🍳 Приготовить", key=f"pick_{idx}", use_container_width=True):
                        with st.spinner(f"Расписываю рецепт и считаю граммовку: {idea['title']}..."):
                            try:
                                res = fetch_single_recipe(api_key, selected, meal, time_lim, wishes, sport_mode, ai_photo, idea["title"])
                                st.session_state.history.append(res)
                                st.session_state.current = res
                                st.rerun()
                            except Exception as e:
                                st.error(f"🚨 Ошибка: {e}")
            st.divider()

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
                            st.markdown("**🛒 Ингредиенты (точный расчёт цен):**")
                            for ing in m_ings: st.markdown(f"- {ing}")
                        if m_steps:
                            st.markdown("**👨‍🍳 Подробное приготовление:**")
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
                m3.metric("🔥 Калории / 100г", rec["cal"])
                m4.metric("💰 Точный бюджет", rec.get("cost", "~220 ₽"))
                st.caption(f"**БЖУ:** {rec['macros']}")
                st.divider()

                st.markdown("### 🛒 Ингредиенты (точный расчёт по граммовке):")
                for i, ing in enumerate(rec["ings"]):
                    st.checkbox(ing, key=f"ing_{rec['title']}_{i}")

                if rec.get("spices"):
                    st.warning(f"🧂 **Подходящие специи:** {rec['spices']}")

                st.markdown("### 👨‍🍳 Подробное приготовление:")
                for i, step in enumerate(rec["steps"], 1):
                    st.checkbox(f"**Шаг {i}.** {step}", key=f"step_{rec['title']}_{i}")

                if rec.get("tip"):
                    st.success(f"💡 **Совет шефа:** {rec['tip']}")
                if rec.get("pairing"):
                    st.info(f"🍷 **Идеальное дополнение:** {rec['pairing']}")

                txt = f"{rec['title']} ({rec.get('cost', '')})\n\nСпеции: {rec.get('spices', '')}\n\nИнгредиенты:\n" + "\n".join(rec["ings"]) + "\n\nШаги:\n" + "\n".join(rec["steps"])
                st.download_button("📥 Скачать рецепт (.txt)", txt, file_name="recipe.txt", use_container_width=True)
        elif not st.session_state.ideas:
            st.markdown("### 👋 Добро пожаловать на кухню ИИ-Шефа!")
            st.write("1. Отметьте продукты в меню слева (можно выбрать хоть весь холодильник — шеф сам отберет сочетаемые).")
            st.write("2. Нажмите **«Подобрать 3 блюда на выбор»** и кликните на понравившийся вариант.")
            st.write("3. Или переключитесь на **«Рацион на весь день»** для готового меню с фото и точным бюджетом.")
            st.info("💡 Все открытые рецепты и рационы сохраняются в левой панели.")
