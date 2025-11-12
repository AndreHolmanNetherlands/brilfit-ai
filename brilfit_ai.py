import streamlit as st
import requests
import os
import numpy as np
from PIL import Image
from io import BytesIO

# === WooCommerce ===
BASE_URL = os.getenv("WOOCOMMERCE_URL", "https://elzeroptiek.nl")
KEY = os.getenv("WOOCOMMERCE_KEY")
SECRET = os.getenv("WOOCOMMERCE_SECRET")

@st.cache_data(ttl=3600)
def get_products():
    if not KEY or not SECRET:
        st.warning("API keys ontbreken")
        return []
    try:
        url = f"{BASE_URL}/wp-json/wc/v3/products"
        auth = (KEY, SECRET)
        params = {"per_page": 100, "status": "publish"}
        r = requests.get(url, auth=auth, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            products = []
            for p in data:
                img = next((i["src"] for i in p.get("images", [])), "")
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                products.append({
                    "name": p["name"],
                    "image": img,
                    "price": p["price"] or "0",
                    "url": p["permalink"],
                    "style": meta.get("style", "ovaal").lower(),
                    "lens_width": int(meta.get("lens_width", 50))
                })
            return products
    except:
        pass
    # Fallback
    return [
        {"name": "Dutz 2270", "image": "https://via.placeholder.com/200x100/0066CC/FFFFFF?text=Dutz", "price": "189", "url": "https://elzeroptiek.nl", "style": "rond", "lens_width": 52},
        {"name": "BBIG 243", "image": "https://via.placeholder.com/200x100/FF6600/FFFFFF?text=BBIG", "price": "149", "url": "https://elzeroptiek.nl", "style": "rechthoekig", "lens_width": 48}
    ]

products = get_products()

# === Simpele gezichtsanalyse (alleen breedte/hoogte ratio) ===
def get_face_shape(w, h):
    ratio = w / h
    if ratio > 0.9: return "ovaal"
    if ratio < 0.75: return "rond"
    return "rechthoekig"

# === Try-on zonder OpenCV (alleen Pillow) ===
def try_on(face_img, bril_url, lens_width):
    try:
        bril = Image.open(BytesIO(requests.get(bril_url, timeout=5).content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (200, 80), (100,100,100,200))
    
    face = face_img.copy().convert("RGBA")
    face_w, face_h = face.size
    
    # Schaal bril
    scale = face_w * 0.6 / lens_width
    new_w = int(bril.width * scale)
    new_h = int(bril.height * scale)
    bril = bril.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Plaats op gezicht
    x = (face_w - new_w) // 2
    y = int(face_h * 0.3)
    face.paste(bril, (x, y), bril)
    return face

# === App ===
st.title("BrilFit AI – Elzer Optiek")
st.write("Probeer brillen virtueel!")

if st.button("Producten vernieuwen"):
    st.cache_data.clear()
    st.rerun()

st.write(f"**{len(products)} brillen beschikbaar**")

col1, col2 = st.columns(2)
with col1:
    st.write("**Selfie uploaden**")
    uploaded = st.file_uploader("", type=["jpg", "png"], key="photo")
with col2:
    st.write("**Of kies vorm**")
    shape = st.selectbox("", ["ovaal", "rond", "rechthoekig"])

if uploaded:
    face_img = Image.open(uploaded)
    st.image(face_img, width=200)
    w, h = face_img.size
    shape = get_face_shape(w, h)
    st.success(f"Gezichtsanalyse: **{shape}**")

if st.button("Zoek mijn bril"):
    matches = [p for p in products if shape in p["style"]]
    if not matches:
        matches = products[:3]
        st.info("Geen exacte match – dit zijn suggesties")
    
    for p in matches:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(p["image"], width=120)
            st.write(f"**{p['name']}**")
            st.write(f"€{p['price']}")
            st.markdown(f"[Kopen ›]({p['url']})")
        with c2:
            if uploaded:
                result = try_on(face_img, p["image"], p["lens_width"])
                st.image(result, caption="Try-on", width=250)
