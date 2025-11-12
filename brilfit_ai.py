import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import os
import uuid

# === WooCommerce ===
BASE_URL = os.getenv("WOOCOMMERCE_URL", "https://elzeroptiek.nl")
KEY = os.getenv("WOOCOMMERCE_KEY")
SECRET = os.getenv("WOOCOMMERCE_SECRET")

@st.cache_data(ttl=3600)
def get_products():
    if not KEY or not SECRET:
        st.warning("API keys ontbreken – fallback brillen getoond")
        return fallback_products()
    
    try:
        r = requests.get(
            f"{BASE_URL}/wp-json/wc/v3/products",
            auth=(KEY, SECRET),
            params={"per_page": 20, "status": "publish"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            products = []
            for p in data:
                img_url = p.get("images", [{}])[0].get("src", "") if p.get("images") else ""
                if not img_url:
                    continue
                products.append({
                    "name": p["name"],
                    "image": img_url,
                    "price": p.get("price", "0"),
                    "url": p.get("permalink", "#"),
                    "lens_width": 50
                })
            return products[:6] if products else fallback_products()
    except:
        pass
    return fallback_products()

def fallback_products():
    return [
        {"name": "Dutz 2270", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/dutz-2270-25-600x600.jpg", "price": "189", "url": "https://elzeroptiek.nl/product/dutz-2270-25/", "lens_width": 52},
        {"name": "BBIG 243", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/bbig-243-465-600x600.jpg", "price": "149", "url": "https://elzeroptiek.nl/product/bbig-243-465/", "lens_width": 48},
        {"name": "Prodesign 1791", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/prodesign-1791-6031-600x600.jpg", "price": "229", "url": "https://elzeroptiek.nl/product/prodesign-1791-6031/", "lens_width": 54}
    ]

products = get_products()

# === Try-on ===
def try_on(face_img, bril_url, lens_width=50):
    try:
        bril = Image.open(BytesIO(requests.get(bril_url, timeout=10).content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (220, 90), (0, 0, 0, 255))  # Zichtbaar zwart frame
    
    face = face_img.copy().convert("RGBA")
    w, h = face.size
    scale = (w * 0.7) / max(lens_width, 40)
    bril = bril.resize((int(bril.width * scale), int(bril.height * scale)), Image.Resampling.LANCZOS)
    face.paste(bril, ((w - bril.width)//2, int(h * 0.25)), bril)
    return face

# === App ===
st.set_page_config(page_title="BrilFit AI – Elzer Optiek", layout="wide")
st.title("BrilFit AI – Elzer Optiek")
st.markdown("**Upload een selfie en zie direct welke bril bij jou past!**")

# Unieke key per upload
upload_key = f"uploader_{uuid.uuid4().hex[:8]}"
uploaded_file = st.file_uploader(
    "Foto (recht van voren, goed licht)", 
    type=["jpg", "jpeg", "png"], 
    key=upload_key
)

face_img = None
if uploaded_file is not None:
    try:
        face_img = Image.open(uploaded_file)
        st.image(face_img, width=300, caption="Jouw selfie – klaar voor try-on!")
    except Exception as e:
        st.error(f"Fout bij laden: {e}")

if st.button("Zoek mijn perfecte bril", type="primary"):
    st.success(f"**{len(products)} brillen geladen!**")
    for p in products:
        c1, c2 = st.columns(2)
        with c1:
            st.image(p["image"], width=180)
            st.markdown(f"**{p['name']}**")
            st.write(f"**€ {p['price']}**")
            st.markdown(f"[Kopen ›]({p['url']})")
        with c2:
            if face_img:
                result = try_on(face_img, p["image"], p["lens_width"])
                st.image(result, caption=f"Try-on: {p['name']}", width=300)
            else:
                st.info("Upload een foto om de bril te proberen!")

st.markdown("---")
st.caption("**Tip**: Voeg featured images toe in WooCommerce voor echte brilfoto's!")
