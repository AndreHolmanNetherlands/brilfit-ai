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
                    continue  # Skip zonder image
                
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                products.append({
                    "name": p["name"],
                    "image": img_url,
                    "price": p.get("price", "0"),
                    "url": p.get("permalink", "#"),
                    "lens_width": int(meta.get("lens_width", 50))
                })
            if products:
                return products[:6]
    except Exception as e:
        st.error(f"WooCommerce fout: {e}")
    
    return fallback_products()  # Altijd fallback als API leeg

def fallback_products():
    return [
        {"name": "Dutz 2270", "image": "https://via.placeholder.com/200x100/000000/FFFFFF?text=DUTZ", "price": "189", "url": "https://elzeroptiek.nl/product/dutz-2270-25/", "lens_width": 52},
        {"name": "BBIG 243", "image": "https://via.placeholder.com/200x100/FF0000/FFFFFF?text=BBIG", "price": "149", "url": "https://elzeroptiek.nl/product/bbig-243-465/", "lens_width": 48},
        {"name": "Prodesign 1791", "image": "https://via.placeholder.com/200x100/0066CC/FFFFFF?text=PRO", "price": "229", "url": "https://elzeroptiek.nl/product/prodesign-1791-6031/", "lens_width": 54}
    ]

products = get_products()

# === Try-on (betere fallback: zwart frame) ===
def try_on(face_img, bril_url, lens_width=50):
    try:
        bril_resp = requests.get(bril_url, timeout=10)
        if bril_resp.status_code == 200:
            bril = Image.open(BytesIO(bril_resp.content)).convert("RGBA")
        else:
            raise Exception("Geen image")
    except:
        # Zichtbare fallback: zwart frame
        bril = Image.new("RGBA", (200, 80), (0, 0, 0, 255))  # Zwart, ondoorzichtig
    
    face = face_img.copy().convert("RGBA")
    w, h = face.size
    scale = (w * 0.7) / max(lens_width, 40)
    bril = bril.resize((int(bril.width * scale), int(bril.height * scale)), Image.Resampling.LANCZOS)
    x = (w - bril.width) // 2
    y = int(h * 0.25)
    face.paste(bril, (x, y), bril)
    return face

# === App ===
st.set_page_config(page_title="BrilFit AI – Elzer Optiek", layout="wide")
st.title("🕶️ BrilFit AI – Elzer Optiek")
st.markdown("**Upload een selfie en zie direct welke bril bij jou past!**")

uploaded_file = st.file_uploader(
    "Foto (recht van voren, glimlach!)", 
    type=["jpg", "jpeg", "png"], 
    key="uploader"
)

face_img = None
if uploaded_file:
    face_img = Image.open(uploaded_file)
    st.image(face_img, width=280, caption="Jouw selfie")

if st.button("Zoek mijn perfecte bril", type="primary"):
    if not products:
        st.error("Geen brillen – check API keys")
    else:
        st.success(f"**{len(products)} brillen geladen!** (Voeg images toe in WP voor echte foto's)")
        for p in products:
            col1, col2 = st.columns(2)
            with col1:
                st.image(p["image"], width=160)
                st.markdown(f"**{p['name']}**")
                st.write(f"€ {p['price']}")
                st.markdown(f"[Kopen ›]({p['url']})")
            with col2:
                if face_img:
                    result = try_on(face_img, p["image"], p["lens_width"])
                    st.image(result, caption=f"Try-on: {p['name']}", width=280)
                else:
                    st.info("Upload foto voor try-on")

st.markdown("---")
st.info("**Tip**: Voeg featured images toe in WooCommerce (wp-admin > Producten > Bewerk) voor echte bril-foto's!")
