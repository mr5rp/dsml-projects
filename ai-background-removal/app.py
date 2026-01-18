import streamlit as st
from PIL import Image
from rembg import remove
import numpy as np
import io

# ---- Color config ----
color_presets = {
    "White": (255, 255, 255),
    "Black": (0, 0, 0),
    "Light Blue": (173, 216, 230),
    "Transparent": None,
    "Custom": None
}

# ---- Streamlit UI Tweaks ----
st.set_page_config(page_title="AI Passport Photo", layout="centered")
st.title("📸 AI-Powered Passport Photo Generator")
st.markdown(
    '<p style="font-size:18px; color:#3d6cb9;">Upload a photo, select a background, and create your passport photo instantly!</p>',
    unsafe_allow_html=True)
st.divider()
st.subheader("Choose a background color")
choice = st.radio("Choose background color", list(color_presets.keys()), horizontal=True)

if choice == "Custom":
    hexval = st.color_picker("Pick any color you like:", "#bfefff")
    bg_rgb = tuple(int(hexval.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    transparent = False
elif choice == "Transparent":
    bg_rgb = None
    transparent = True
else:
    bg_rgb = color_presets[choice]
    transparent = False

st.subheader("Upload your image")
uploaded_file = st.file_uploader("Upload an image:", type=["jpg", "jpeg", "png"])

def process_passport_photo_pil(input_img, bg_rgb, transparent=False, target_size=(1200, 1200)):
    output = remove(input_img)
    output_np = np.array(output).copy()
    if transparent:
        return Image.fromarray(output_np, "RGBA")
    h, w, _ = output_np.shape
    bg = np.array(bg_rgb, dtype=np.uint8)
    bg = np.tile(bg, (h, w, 1))
    alpha = output_np[:, :, 3] / 255.0
    for c in range(3):
        output_np[:, :, c] = (alpha * output_np[:, :, c] +
                              (1 - alpha) * bg[:, :, c])
    final_img = Image.fromarray(output_np).convert("RGB")
    def resize_with_padding(img, target_size=target_size, bg_color=(255, 255, 255)):
        old_size = img.size
        ratio = min(target_size[0] / old_size[0], target_size[1] / old_size[1])
        new_size = (int(old_size[0] * ratio), int(old_size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGB", target_size, bg_color)
        new_img.paste(img, ((target_size[0] - new_size[0]) // 2,
                            (target_size[1] - new_size[1]) // 2))
        return new_img
    final_img = resize_with_padding(final_img, target_size, bg_color=bg_rgb)
    return final_img

if uploaded_file:
    input_img = Image.open(uploaded_file).convert("RGBA")
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.image(input_img, caption="Original Photo", use_container_width=True)
    result_img = None
    st.write("")
    if st.button("Generate Passport Photo", use_container_width=True):
        with st.spinner("Processing..."):
            result_img = process_passport_photo_pil(input_img, bg_rgb, transparent)
            if result_img:
                st.success("Done! See your passport photo on the right side.")
    with col2:
        if result_img:
            st.image(result_img, caption="Passport Photo", use_container_width=True)
            img_buffer = io.BytesIO()
            if transparent:
                result_img.save(img_buffer, format="PNG")
                download_name = "passport_photo.png"
            else:
                result_img.save(img_buffer, format="JPEG", quality=100, dpi=(300, 300))
                download_name = "passport_photo.jpg"
            st.download_button("Download Passport Photo", img_buffer.getvalue(), file_name=download_name)