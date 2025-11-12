import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import os

# === WooCommerce ===
BASE_URL = os.getenv("WOOCOMMERCE_URL", "https://elzeroptiek.nl")
KEY = os.getenv("WOOCOMMERCE_KEY")
SECRET = os.getenv("WOOCOMMERCE_SECRET")

@st.cache_data(ttl=3600)
def get_products():
    if not KEY or not SECRET:
        return []
    try:
        r = requests.get(
            f"{BASE_URL}/wp-json/wc/v3/products",
            auth=(KEY, SECRET),
            params={"per_page": 100},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            return [{
                "name": p["name"],
                "image": p["images"][0]["src"] if p["images"] else "",
                "price": p["price"],
                "url": p["permalink"],
                "style": "ovaal"  # later aanpassen
            } for p in data if p["in_stock"]]
    except:
        pass
    return [
        {"name": "Dutz 2270", "image": "https://via.placeholder.com/200x100/0066CC/FFFFFF?text=Dutz", "price": "189", "url": "https://elzeroptiek.nl", "style": "rond"},
        {"name": "BBIG 243", "image": "https://via.placeholder.com/200x100/FF6600/FFFFFF?text=BBIG", "price": "149", "url": "https://elzeroptiek.nl", "style": "rechthoekig"}
    ]

products = get_products()

# === Try-on (alleen Pillow) ===
def try_on(face, bril_url):
    try:
        bril = Image.open(BytesIO(requests.get(bril_url, timeout=5).content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (180, 70), (100,100,100,200))
    
    face = face.copy().convert("RGBA")
    w, h = face.size
    bril = bril.resize((int(w*0.6), int(w*0.6*0.4)), Image.Resampling.LANCZOS)
    face.paste(bril, (int(w*0.2), int(h*0.3)), bril)
    return face

# === App ===
st.title("BrilFit AI")
st.write("Upload een selfie en probeer brillen!")

uploaded = st.file_uploader("Foto", type=["jpg", "png"])
if uploaded:
    img = Image.open(uploaded)
    st.image(img, width=200)

if st.button("Zoek brillen"):
    for p in products[:3]:
        c1, c2 = st.columns(2)
        with c1:
            st.image(p["image"], width=100)
            st.write(p["name"])
            st.markdown(f"[Kopen]({p['url']})")
        with c2:
            if uploaded:
                st.image(try_on(img, p["image"]), width=200)
