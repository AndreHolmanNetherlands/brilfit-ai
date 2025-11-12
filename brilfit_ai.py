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
                # Juiste afbeelding ophalen
                img_url = ""
                if p.get("images") and len(p["images"]) > 0:
                    img_url = p["images"][0]["src"]
                
                # Meta data
                meta = {m["key"]: m["value"] for m in p.get("meta_data", [])}
                style = meta.get("style", "ovaal").lower()
                lens_width = int(meta.get("lens_width", 50))
                
                products.append({
                    "name": p["name"],
                    "image": img_url or "https://via.placeholder.com/200x100/cccccc/666666?text=Bril",
                    "price": p.get("price", "0"),
                    "url": p.get("permalink", "#"),
                    "style": style,
                    "lens_width": lens_width
                })
            return [p for p in products if p["image"].startswith("http")][:6]
    except Exception as e:
        st.error(f"WooCommerce fout: {e}")
    
    # Fallback met echte afbeeldingen van jouw site
    return [
        {"name": "Dutz 2270", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/dutz-2270-25-600x600.jpg", "price": "189", "url": "https://elzeroptiek.nl/product/dutz-2270-25/", "style": "rond", "lens_width": 52},
        {"name": "BBIG 243", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/bbig-243-465-600x600.jpg", "price": "149", "url": "https://elzeroptiek.nl/product/bbig-243-465/", "style": "rechthoekig", "lens_width": 48},
        {"name": "Prodesign 1791", "image": "https://elzeroptiek.nl/wp-content/uploads/2024/09/prodesign-1791-6031-600x600.jpg", "price": "229", "url": "https://elzeroptiek.nl/product/prodesign-1791-6031/", "style": "ovaal", "lens_width": 54}
    ]

products = get_products()

# === Try-on (Pillow) ===
def try_on(face_img, bril_url, lens_width=50):
    try:
        bril_resp = requests.get(bril_url, timeout=10)
        if bril_resp.status_code != 200:
            raise Exception("Afbeelding niet gevonden")
        bril = Image.open(BytesIO(bril_resp.content)).convert("RGBA")
    except:
        bril = Image.new("RGBA", (200, 80), (200,200,200,180))
    
    face = face_img.copy().convert("RGBA")
    w, h = face.size
    scale = (w * 0.65) / max(lens_width, 40)
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
st.markdown("### Upload een selfie en zie direct welke bril bij jou past!")

# File uploader met unieke key om 400 te voorkomen
uploaded_file = st.file_uploader(
    "Foto (recht van voren, goed licht)",
    type=["jpg", "jpeg", "png"],
    key="photo_uploader",
    help="Max 5MB"
)

face_img = None
if uploaded_file is not None:
    try:
        face_img = Image.open(uploaded_file)
        st.image(face_img, width=250, caption="Jouw selfie")
    except Exception as e:
        st.error(f"Fout bij laden foto: {e}")

if st.button("Zoek mijn perfecte bril", type="primary"):
    if not products:
        st.error("Geen brillen gevonden – controleer API keys")
    else:
        st.success(f"**{len(products)} brillen geladen uit jouw winkel!**")
        for p in products:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(p["image"], width=150, use_column_width=True)
                st.markdown(f"**{p['name']}**")
                st.write(f"**€ {p['price']}**")
                st.markdown(f"[Direct kopen ›]({p['url']})")
            with col2:
                if face_img:
                    try:
                        result = try_on(face_img, p["image"], p["lens_width"])
                        st.image(result, caption=f"Try-on: {p['name']}", width=250)
                    except Exception as e:
                        st.warning(f"Try-on mislukt: {e}")
                else:
                    st.info("Upload een foto om try-on te zien")
