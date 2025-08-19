import streamlit as st
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import gspread
import pandas as pd
from io import BytesIO
from google.oauth2 import service_account

# Streamlit Title
st.title("Barcode Generator with Image")

# Google Sheets Authentication
google_cloud_secrets = st.secrets["google_cloud"]
creds = service_account.Credentials.from_service_account_info(
    {
        "type": google_cloud_secrets["type"],
        "project_id": google_cloud_secrets["project_id"],
        "private_key_id": google_cloud_secrets["private_key_id"],
        "private_key": google_cloud_secrets["private_key"].replace("\\n", "\n"),
        "client_email": google_cloud_secrets["client_email"],
        "client_id": google_cloud_secrets["client_id"],
        "auth_uri": google_cloud_secrets["auth_uri"],
        "token_uri": google_cloud_secrets["token_uri"],
        "auth_provider_x509_cert_url": google_cloud_secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": google_cloud_secrets["client_x509_cert_url"],
        "universe_domain": google_cloud_secrets["universe_domain"],
    },
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)

client = gspread.authorize(creds)
spreadsheet_id = "15at-sHNUtXCZZMT-COgbdg4u_IMdhrMgx9BfgbNjINg"

# Function to Get Data from Google Sheet
def get_data(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name).get_all_records()
    df_sheet = pd.DataFrame(sheet)
    return df_sheet

if "master" not in st.session_state:
    with st.spinner("Updating Master Data . . ."):
        st.session_state.master = get_data("NEWLIST")

st.dataframe(st.session_state.master)

# Select Item Code
itemcodes = st.selectbox("Select ItemCode", st.session_state.master["ItemCode"].unique())
foto_loading = st.file_uploader("Upload Foto Loading", type=["jpg", "jpeg", "png"])
sequence_number = str(st.session_state.master[st.session_state.master["ItemCode"] == itemcodes]["SequenceNumber"].values[0])

if itemcodes:
    # Generate barcode
    barcode_format = barcode.get_barcode_class('code128')
    barcode_object = barcode_format(sequence_number, writer=ImageWriter())

    barcode_bytes = BytesIO()
    barcode_object.write(barcode_bytes, {"module_height": 8, "module_width": 0.3, "dpi": 200, "font_size": 5})
    barcode_bytes.seek(0)
    barcode_image = Image.open(barcode_bytes)

    st.image(barcode_image, width=300, caption="Generated Barcode")

if st.button("Generate with Foto") and foto_loading is not None:
    # Load Foto
    img = Image.open(foto_loading).convert("RGBA")
    img = img.resize((750, 750))

    # Buat Template
    template = Image.new("RGBA", (800, 1200), "white")
    
    # Tempelkan Foto Loading
    image_x = (template.width - img.width) // 2
    image_y = 25
    template.paste(img, (image_x, image_y))

    # Tambah Text
    draw = ImageDraw.Draw(template)
    
    # Tambahkan teks (ItemCode) di bawah foto
    font_size = 40
    try:
        font = ImageFont.truetype("Poppins-Medium.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text = f"{itemcodes}"
    text_x = (template.width - draw.textlength(text, font=font)) // 2
    text_y = image_y + img.height + 20
    draw.text((text_x, text_y), text, fill="black", font=font)

    # Hitung tinggi teks agar barcode tidak menimpa teks
    text_height = font_size + 5  # Perkiraan tinggi teks dengan margin
    barcode_image = barcode_image.resize((int(barcode_image.width * 1.5), int(barcode_image.height * 1.5)))
    # Tempelkan Barcode di bawah teks
    barcode_x = (template.width - barcode_image.width) // 2
    barcode_y = text_y + text_height + 20  # Jarak 20px dari teks
    template.paste(barcode_image, (barcode_x, barcode_y))

    st.image(template, width=800)

    # Simpan & Download
    buf = BytesIO()
    template.save(buf, "PNG")
    st.download_button("Download", buf.getvalue(), f"{itemcodes}.png", "image/png")
