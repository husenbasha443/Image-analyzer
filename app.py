"""
Image Analyzer Web App
Professional UI + Stable Azure Computer Vision API
"""

import streamlit as st
import requests
from PIL import Image
import os
import io
from dotenv import load_dotenv


load_dotenv()

AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
AZURE_VISION_API_KEY = os.getenv("AZURE_VISION_API_KEY")

SUPPORTED_FORMATS = ["jpg", "jpeg", "png"]


st.set_page_config(
    page_title="Image Analyzer",
    page_icon="🖼️",
    layout="centered"
)

st.markdown("""
<style>
body { background-color:#0b1220; }
.block-container { max-width:900px; padding-top:2rem; }

.header {
    text-align:center;
    margin-bottom:2.5rem;
}
.header h1 {
    font-size:2.4rem;
    margin-bottom:0.2rem;
}
.header p {
    color:#9ca3af;
    font-size:1rem;
}

.section {
    margin-top:2.2rem;
}

.card {
    background:#111827;
    border:1px solid #1f2937;
    border-radius:14px;
    padding:1.2rem;
}

.image-box {
    display:flex;
    justify-content:center;
    margin-top:1.2rem;
}

.tag {
    display:inline-block;
    padding:6px 14px;
    border-radius:999px;
    background:#0f172a;
    border:1px solid #334155;
    margin:4px;
    font-size:0.9rem;
    color:#e5e7eb;
}

.object-card {
    background:#0f172a;
    border:1px solid #334155;
    border-radius:12px;
    padding:0.9rem;
    margin-bottom:0.8rem;
}

small { color:#9ca3af; }
hr { border:0; border-top:1px solid #1f2937; margin:3rem 0; }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="header">
    <h1>🖼️ Image Analyzer</h1>
    <p>Analyze images using Azure Computer Vision</p>
</div>
""", unsafe_allow_html=True)


if not AZURE_VISION_ENDPOINT or not AZURE_VISION_API_KEY:
    st.error("Azure Computer Vision credentials missing in .env")
    st.stop()

st.markdown("## Upload Image")
uploaded_file = st.file_uploader(
    "Select an image file (JPG / PNG)",
    type=SUPPORTED_FORMATS
)


if uploaded_file:
    image = Image.open(uploaded_file)

    st.markdown('<div class="image-box">', unsafe_allow_html=True)
    st.image(image, width=520)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


    if st.button("🔍 Analyze Image"):
        with st.spinner("Analyzing image..."):
            # Rewind and re-encode the image into a clean JPEG buffer.
            # This avoids InvalidImageFormat errors from exotic encodings.
            uploaded_file.seek(0)
            pil_img = Image.open(uploaded_file).convert("RGB")
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG")
            image_bytes = buf.getvalue()

            url = f"{AZURE_VISION_ENDPOINT.rstrip('/')}/vision/v3.2/analyze"
            params = {"visualFeatures": "Description,Objects,Tags"}
            headers = {
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": AZURE_VISION_API_KEY
            }

            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=image_bytes,
                timeout=30
            )

            if response.status_code != 200:
                st.error(response.text)
                st.stop()

            result = response.json()


        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("## 📄 Image Description")

        if result.get("description", {}).get("captions"):
            cap = result["description"]["captions"][0]

            # Main caption card
            st.markdown(f"""
            <div class="card">
                <h3>{cap['text']}</h3>
                <small>Confidence: {cap['confidence']*100:.1f}%</small>
            </div>
            """, unsafe_allow_html=True)

            # Extra feature: short paragraph (≤ 100 words) in simple English
            objects = [o["object"] for o in result.get("objects", [])][:5]
            tags = [t["name"] for t in result.get("tags", [])][:5]

            # Build a simple narrative sentence
            details_parts = []
            if objects:
                details_parts.append(
                    "It seems to show " + ", ".join(o for o in objects)
                )
            if tags:
                details_parts.append(
                    "The scene relates to " + ", ".join(t for t in tags)
                )

            base_sentence = f"The AI thinks this image is about {cap['text']}."
            extra_sentence = ""
            if details_parts:
                extra_sentence = " " + ". ".join(details_parts) + "."

            paragraph = (base_sentence + extra_sentence).strip()
            # Hard cap at ~100 words
            words = paragraph.split()
            if len(words) > 100:
                paragraph = " ".join(words[:100]) + "..."

            st.markdown("#### 🗒️ Summary (within 100 words)")
            st.markdown(
                f"<p style='color:#e5e7eb; line-height:1.6;'>{paragraph}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("No description detected")
        st.markdown('</div>', unsafe_allow_html=True)


        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("## 🎯 Detected Objects")

        if result.get("objects"):
            cols = st.columns(2)
            for i, obj in enumerate(result["objects"]):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="object-card">
                        <strong>{obj['object'].title()}</strong><br>
                        <small>Confidence: {obj['confidence']*100:.1f}%</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No objects detected")
        st.markdown('</div>', unsafe_allow_html=True)


        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("## 🏷️ Image Tags")

        if result.get("tags"):
            tags_html = ""
            for tag in result["tags"]:
                tags_html += f"""
                <span class="tag">
                    {tag['name']} ({tag['confidence']*100:.0f}%)
                </span>
                """
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.warning("No tags detected")
        st.markdown('</div>', unsafe_allow_html=True)


        with st.expander("📄 Raw API Response"):
            st.json(result)

st.markdown("""
<hr>
<p style="text-align:center;color:#6b7280;font-size:0.85rem;">
Powered by Azure Computer Vision • AI results are probabilistic
</p>
""", unsafe_allow_html=True)