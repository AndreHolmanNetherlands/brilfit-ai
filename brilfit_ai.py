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
        st.warning("API keys ontbreken – fallback brillen getoond")
        return []
    
    try:
        r = requests.get(
            f"{BASE_URL}/wp-json/wc/v3/products",
            auth=(KEY, SECRET),
            params={"per_page": 50, "status": "publish", "category": "brillen"},  # optioneel: alleen brillen
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            products = []
            for p in data:
                img = p.get("images", [{}])[0].get("src", "") if p.get("images") else ""
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                style = meta.get("style", "ovaal").lower()
                products.append({
                    "name": p["name"],
                    "image": img or "https://via.placeholder.com/200x100?text=Bril",
                    "price": p["price"] or "0",
                    "url": p["permalink"],
                    "style": style,
                    "lens_width": int(meta.get("lens_width", 50))
                })
            return [p for p in products if p["image"] != ""][:12]  # max 12
    except Exception as e:
        st.error(f"Fout met WooCommerce: {e}")
    
    # Fallback als API faalt
    return [
        {"name": "Dutz 2270", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/dutz-2270-25-600x600.jpg", "price": "189", "url": "https://elzeroptiek.nl", "style": "rond", "lens_width": 52},
        {"name": "BBIG 243", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/bbig-243-465-600x600.jpg", "price": "149", "url": "https://elzeroptiek.nl", "style": "rechthoekig", "lens_width": 48},
        {"name": "Prodesign 1791", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/prodesign-1791-6031-600x600.jpg", "price": "229", "url": "https://elzeroptiek.nl", "style": "ovaal", "lens_width": 54}
    ]

products = get_products()

# === Try-on (Pillow) ===
def try_on(face_img, bril_url, lens_width=50):
    try:
        bril = Image.open(BytesIO(requests.get(bril_url, timeout=10).content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (200, 80), (200,200,200,180))
    
    face = face_img.copy().convert("RGBA")
    w, h = face.size
    scale = (w * 0.65) / lens_width
    new_w = int(bril.width * scale)
    new_h = int(bril.height * scale)
    bril = bril.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    x = (w - new_w) // 2
    y = int(h * 0.28)
    face.paste(bril, (x, y), bril)
    return face

# === App ===
st.set_page_config(page_title="BrilFit AI – Elzer Optiek", layout="centered")
st.title("BrilFit AI")
st.write("Upload een selfie en zie direct welke bril bij jou past!")

uploaded = st.file_uploader("Foto (recht van voren)", type=["jpg", "png", "jpeg"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, width=250, caption="Jouw selfie")

if st.button("Zoek mijn perfecte bril", type="primary"):
    if not products:
        st.error("Geen brillen gevonden – check WooCommerce API keys")
    else:
        st.success(f"{len(products)} brillen geladen!")
        for p in products:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(p["image"], width=140)
                st.write(f"**{p['name']}**")
                st.write(f"€ {p['price']}")
                st.markdown(f"[Direct kopen ›]({p['url']})")
            with col2:
                if uploaded:
                    result = try_on(img, p["image"], p["lens_width"])
                    st.image(result, caption=f"Try-on: {p['name']}", width=250)
