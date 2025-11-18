import streamlit as st
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import gspread
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval
from io import BytesIO
import pandas as pd
from google.oauth2 import service_account

# Databases
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

def get_data(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name).get_all_records()
    return pd.DataFrame(sheet)

def input_data(generate_code, generate_desc, sequence_number, kategori, subitem, checking_code, akronim):
    st.session_state.master = get_data("Master")
    akronim_now = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Initial'].values[0]
    count_akronim_now = st.session_state.master['ItemCode'].str.contains(akronim_now).sum()
    checking_code_now = f"{akronim_now}-{count_akronim_now+1:04d}"

    if checking_code != checking_code_now:
        st.error("Lebih dari satu user membuat code dengan Sub Item ini. Silahkan coba lagi.")
        st.stop()
    if generate_code in st.session_state.master['ItemCode'].unique():
        st.error("Code already exists.")
        st.stop()
    if generate_desc in st.session_state.master['ItemName'].unique():
        st.error("Description already exists.")
        st.stop()
    if sequence_number in st.session_state.master['SequenceNumber'].unique():
        st.error("Sequence Number already exists.")
        st.stop()

    sheet = client.open_by_key(spreadsheet_id).worksheet("Master")
    sheet.append_row([generate_code, generate_desc, sequence_number, kategori, subitem, akronim], value_input_option="USER_ENTERED")

# Load Data
if "numbering_sub" not in st.session_state:
    with st.spinner("Updating Numbering Sub Data..."):
        st.session_state.numbering_sub = get_data("Numbering Sub")

if "numbering_kategori" not in st.session_state:
    with st.spinner("Updating Numbering Kategori Data..."):
        st.session_state.numbering_kategori = get_data("Numbering Kategori")

if "master" not in st.session_state:
    with st.spinner("Updating Master Data..."):
        st.session_state.master = get_data("Master")

@st.cache_data(ttl=600)
def get_cached_item_master():
    return get_data("ItemMaster")

# Input UI
kategori = st.selectbox("Kategori", options=["Pilih Kategori"] + sorted(st.session_state.numbering_kategori['Item Group']))
subitem = st.selectbox("Subitem", options=sorted(st.session_state.numbering_sub[st.session_state.numbering_sub['Kategori'] == kategori]['Sub Item'].unique()))
desc1 = st.text_input("Desc1", value=subitem, disabled=True)
desc2 = st.text_input("Desc2", value="")

if desc1 and desc2:
    generate_desc = (desc1 + " " + desc2).strip().upper()

if desc2 and kategori != "Pilih Kategori":
    tahun = "26"
    akronim = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Initial'].values[0]
    num_initial = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Number of Sequence'].values[0]
    kategori_sub_count = st.session_state.master[st.session_state.master['Sub Item'] == subitem]['ItemCode'].count()

    list_codes = st.session_state.master[st.session_state.master['Sub Item'] == subitem]['ItemCode'].unique()
    count_sub = len(list_codes)
    checking_code = f"{akronim}-{st.session_state.master['ItemCode'].str.contains(akronim).sum() + 1:04d}"

    if count_sub == 0:
        generate_code = f"{akronim}-{num_initial}-1"
    else:
        list_codes = pd.Series(list_codes)
        list_codes = list_codes[list_codes.str.contains("-")]
        list_codes = list_codes[list_codes.apply(lambda x: x.split("-")[-1].isdigit())]
        list_codes = list_codes.astype(str)
        list_codes_digits = list_codes.apply(lambda x: int(x.split("-")[-1]))

        full_range = set(range(list_codes_digits.min(), list_codes_digits.max() + 1))
        missing = sorted(full_range - set(list_codes_digits))

        if missing:
            generate_code = f"{akronim}-{num_initial}-{missing[0]}"
        else:
            generate_code = f"{akronim}-{num_initial}-{count_sub + 1}"

    sequence_number = f"{tahun}{num_initial:06d}{kategori_sub_count + 1:04d}"

    # Barcode generate
    barcode_format = barcode.get_barcode_class('code128')
    barcode_object = barcode_format(sequence_number, writer=ImageWriter())
    barcode_bytes = BytesIO()
    barcode_object.write(barcode_bytes, {"module_height": 8, "module_width": 0.3, "dpi": 200})
    barcode_bytes.seek(0)
    barcode_image = Image.open(barcode_bytes)

    st.text_input("ItemCode", value=generate_code, disabled=True)
    st.text_input("Generated Description", value=generate_desc, disabled=True)
    st.text_input("Sequence Number", value=sequence_number, disabled=True)
    st.image(barcode_image, width=300)

    if generate_desc in st.session_state.master['ItemName'].values:
        st.warning("Deskripsi sudah digunakan.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    if col1.button("Submit"):
        if akronim == "BELUM ADA INITIAL":
            st.warning("Belum ada Initial.")
            st.stop()
        st.session_state.master = get_data("Master")
        if generate_desc in st.session_state.master['ItemName'].values:
            st.warning("Sudah disimpan, silahkan reset.")
        else:
            input_data(generate_code, generate_desc, sequence_number, kategori, subitem, checking_code, akronim)
            st.download_button(
                label="⬇ Download Barcode",
                data=barcode_bytes.getvalue(),
                file_name=f"{generate_code}.png",
                mime="image/png",
            )
            st.success("Masuk Pak Max!!!")
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    if col2.button("Reset"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
