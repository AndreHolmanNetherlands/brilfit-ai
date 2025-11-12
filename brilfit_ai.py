import streamlit as st
import requests
import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

# WooCommerce instellingen
BASE_URL = os.getenv("WOOCOMMERCE_URL", "https://elzeroptiek.nl")
CONSUMER_KEY = os.getenv("WOOCOMMERCE_KEY")
CONSUMER_SECRET = os.getenv("WOOCOMMERCE_SECRET")

@st.cache_data(ttl=3600)
def fetch_products_from_wc():
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        st.warning("WooCommerce API keys nog niet ingesteld.")
        return []
    
    endpoint = f"{BASE_URL}/wp-json/wc/v3/products"
    auth = (CONSUMER_KEY, CONSUMER_SECRET)
    params = {"per_page": 100, "status": "publish"}
    
    try:
        response = requests.get(endpoint, auth=auth, params=params, timeout=10)
        if response.status_code == 200:
            products = response.json()
            parsed = []
            for p in products:
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                sizes = {
                    "lens_width": int(meta.get("lens_width", 50)),
                    "bridge": int(meta.get("bridge", 18)),
                    "temple": int(meta.get("temple", 140))
                }
                style = meta.get("style", "ovaal")
                parsed.append({
                    "name": p.get("name", "Onbekend"),
                    "image_url": next((img["src"] for img in p.get("images", []) if img.get("position") == 0), "https://via.placeholder.com/200?text=No+Image"),
                    "sizes": sizes,
                    "style": style,
                    "price": p.get("price", 0),
                    "url": f"{BASE_URL}/product/{p.get('slug', 'product')}/",
                    "in_stock": p.get("in_stock", True)
                })
            return [p for p in parsed if p["in_stock"]]
        else:
            st.warning(f"Fout bij ophalen producten: {response.status_code}")
            return []
    except:
        st.warning("Geen verbinding met winkel. Gebruik voorbeeldbrillen.")
        return [
            {"name": "Dutz 2270 25", "image_url": "https://via.placeholder.com/200x100?text=Dutz+2270", "sizes": {"lens_width": 52, "bridge": 18, "temple": 140}, "style": "rond", "price": 189, "url": "https://elzeroptiek.nl", "in_stock": True},
            {"name": "BBIG 243 465", "image_url": "https://via.placeholder.com/200x100?text=BBIG+243", "sizes": {"lens_width": 48, "bridge": 16, "temple": 130}, "style": "rechthoekig", "price": 149, "url": "https://elzeroptiek.nl", "in_stock": True}
        ]

COLLECTIE = fetch_products_from_wc()

def detect_face_shape(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        aspect_ratio = w / h
        if aspect_ratio > 0.8:
            return "ovaal"
        elif aspect_ratio < 0.7:
            return "rond"
        else:
            return "rechthoekig"
    return "ovaal"

def get_recommendations(shape, style_pref=""):
    recs = [p for p in COLLECTIE if shape.lower() in p["style"].lower() or (style_pref and style_pref.lower() in p["style"].lower())]
    return recs[:3] if recs else COLLECTIE[:3]

def virtual_try_on(face_image, bril_url, sizes):
    try:
        bril_resp = requests.get(bril_url, timeout=5)
        bril = Image.open(BytesIO(bril_resp.content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (200, 100), (200,200,200,255))
    
    face = np.array(face_image.convert("RGBA"))
    gray = cv2.cvtColor(face, cv2.COLOR_RGBA2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) > 0:
        x, y, w, h = faces[0]
        scale = w / sizes["lens_width"]
        bril_resized = bril.resize((int(bril.width * scale), int(bril.height * scale)), Image.Resampling.LANCZOS)
        x_start = x + (w - bril_resized.width) // 2
        y_start = y + int(h * 0.3)
        
        for i in range(min(bril_resized.height, face.shape[0] - y_start)):
            for j in range(min(bril_resized.width, face.shape[1] - x_start)):
                if 0 <= y_start + i < face.shape[0] and 0 <= x_start + j < face.shape[1]:
                    alpha = bril_resized.getpixel((j, i))[3] / 255.0
                    face[y_start + i, x_start + j] = (
                        int(face[y_start + i, x_start + j][0] * (1 - alpha) + bril_resized.getpixel((j, i))[0] * alpha),
                        int(face[y_start + i, x_start + j][1] * (1 - alpha) + bril_resized.getpixel((j, i))[1] * alpha),
                        int(face[y_start + i, x_start + j][2] * (1 - alpha) + bril_resized.getpixel((j, i))[2] * alpha),
                        255
                    )
    return Image.fromarray(face)

st.title("🕶️ BrilFit AI – Elzer Optiek")
st.write("Upload een selfie of doe de quiz voor persoonlijk briladvies!")

if st.button("Vernieuw producten uit winkel"):
    st.cache_data.clear()
    st.rerun()

st.info(f"Aantal beschikbare brillen: {len(COLLECTIE)}")

input_type = st.radio("Kies je methode:", ("Foto uploaden", "Quiz"))

shape = "ovaal"  # Default
face_image = None

if input_type == "Foto uploaden":
    uploaded = st.file_uploader("Upload een duidelijke selfie (recht van voren)", type=["jpg", "png"])
    if uploaded:
        face_image = Image.open(uploaded)
        st.image(face_image, caption="Jouw foto", width=200)
        shape = detect_face_shape(face_image)
        st.success(f"**Gezichtsanalyse**: {shape.capitalize()} gezicht")
else:
    shape = st.selectbox("Wat is je gezichtsvorm?", ["ovaal", "rond", "rechthoekig", "oblong"])
    st.success(f"**Gekozen**: {shape.capitalize()}")

if st.button("Zoek mijn perfecte bril"):
    recs = get_recommendations(shape)
    if recs:
        st.success(f"{len(recs)} brillen gevonden voor een {shape} gezicht!")
        for rec in recs:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(rec["image_url"], width=120, use_column_width=True)
                st.write(f"**{rec['name']}**")
                st.write(f"€{rec['price']}")
                st.markdown(f"[Kopen ›]({rec['url']})")
            with col2:
                if face_image:
                    try_on = virtual_try_on(face_image, rec["image_url"], rec["sizes"])
                    st.image(try_on, caption=f"Try-on: {rec['name']}", width=250)
    else:
        st.info("Geen matches gevonden – probeer een andere vorm!")
