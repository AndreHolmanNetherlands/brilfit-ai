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
            params={"per_page": 20, "status": "publish"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            products = []
            for p in data:
                img_url = p.get("images", [{}])[0].get("src", "") if p.get("images") else ""
                if not img_url:
                    continue  # skip zonder afbeelding
                
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                products.append({
                    "name": p["name"],
                    "image": img_url,
                    "price": p.get("price", "0"),
                    "url": p.get("permalink", "#"),
                    "lens_width": int(meta.get("lens_width", 50))
                })
            return products[:6] if products else None
    except Exception as e:
        st.error(f"WooCommerce fout: {e}")
    
    # Fallback met echte afbeeldingen
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
        bril = Image.new("RGBA", (200, 80), (200,200,200,180))
    
    face = face_img.copy().convert("RGBA")
    w, h = face.size
    scale = (w * 0.65) / max(lens_width, 40)
    bril = bril.resize((int(bril.width * scale), int(bril.height * scale)), Image.Resampling.LANCZOS)
    face.paste(bril, ((w - bril.width)//2, int(h * 0.28)), bril)
    return face

# === App ===
st.set_page_config(page_title="BrilFit AI – Elzer Optiek", layout="centered")
st.title("BrilFit AI")
st.markdown("### Upload een selfie en zie direct welke bril bij jou past!")

uploaded_file = st.file_uploader(
    "Foto (recht van voren)",
    type=["jpg", "jpeg", "png"],
    key="uploader"
)

face_img = None
if uploaded_file:
    face_img = Image.open(uploaded_file)
    st.image(face_img, width=250, caption="Jouw selfie")

if st.button("Zoek mijn perfecte bril", type="primary"):
    if not products:
        st.error("Geen brillen geladen – controleer API keys")
    else:
        st.success(f"**{len(products)} brillen geladen!**")
        for p in products:
            c1, c2 = st.columns(2)
            with c1:
                st.image(p["image"], width=150)  # GEEN use_column_width
                st.markdown(f"**{p['name']}**")
                st.write(f"**€ {p['price']}**")
                st.markdown(f"[Kopen ›]({p['url']})")
            with c2:
                if face_img:
                    result = try_on(face_img, p["image"], p["lens_width"])
                    st.image(result, caption=f"Try-on: {p['name']}", width=250)
                else:
                    st.info("Upload een foto voor try-on")
