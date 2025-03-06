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

def input_data(generate_code, generate_desc, sequence_number, kategori, subitem, checking_code):
    st.session_state.master = get_data("Master")
    akronim_now = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Initial'].values[0]
    count_akronim_now = st.session_state.master['ItemCode'].str.contains(akronim_now).sum()
    checking_code_now = f"{akronim_now}-{count_akronim_now+1:04d}"

    if checking_code != checking_code_now:
        st.error("Lebih dari satu user membuat code dengan Sub Item ini. Silahkan coba lagi.")
        st.stop()
    

    if generate_code in st.session_state.master['ItemCode'].unique():
        st.error("Code already exists. Please try again.")
        st.stop()
    if generate_desc in st.session_state.master['ItemName'].unique():
        st.error("Description already exists. Please try again.")
        st.stop()
    if sequence_number in st.session_state.master['SequenceNumber'].unique():
        st.error("Sequence Number already exists. Please try again.")
        st.stop()
    sheet = client.open_by_key(spreadsheet_id).worksheet("Master")
    sheet.append_row([generate_code, generate_desc, sequence_number, kategori, subitem], value_input_option="USER_ENTERED")

# Coding UI
if "numbering_sub" not in st.session_state:
    with st.spinner("Updating Numbering Sub Data . . ."):
        st.session_state.numbering_sub = get_data("Numbering Sub")

if "numbering_kategori" not in st.session_state:
    with st.spinner("Updating Numbering Kategori Data . . ."):
        st.session_state.numbering_kategori = get_data("Numbering Kategori")

if "numbering_sequence" not in st.session_state:
    with st.spinner("Updating Numbering Sequence Data . . ."):
        st.session_state.numbering_sequence = get_data("Numbering Sequence")

if "master" not in st.session_state:
    with st.spinner("Updating Master Data . . ."):
        st.session_state.master = get_data("Master")

@st.cache_data(ttl=600)
def get_cached_item_master():
    return get_data("ItemMaster")

kategori = st.selectbox("Kategori", options=["Pilih Kategori"] + sorted(st.session_state.numbering_kategori['Item Group']))
subitem = st.selectbox("Subitem", options=sorted(st.session_state.numbering_sub[st.session_state.numbering_sub['Kategori'] == kategori]['Sub Item'].unique()))
desc1 = st.text_input("Desc1", value=subitem, disabled=True)
desc2 = st.text_input("Desc2", value="")
if desc1 and desc2:
    generate_desc = (desc1 + " " + desc2).strip().upper()





if desc2 and kategori != "Pilih Kategori":
    tahun = datetime.now().year % 100
    akronim = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Initial'].values[0]
    num_kat = st.session_state.numbering_kategori[st.session_state.numbering_kategori['Item Group'] == kategori]['Numbering'].values[0]
    num_sub = st.session_state.numbering_sub[st.session_state.numbering_sub['Sub Item'] == subitem]['Number Of Sub'].values[0]
    count_akronim = st.session_state.master['ItemCode'].str.contains(akronim).sum()
    num_initial = st.session_state.numbering_sequence[st.session_state.numbering_sequence['Sub Item'] == subitem]['InitialCode'].values[0]
    kategori_sub_count = st.session_state.master[st.session_state.master['Sub Item'] == subitem]['ItemCode'].count()
    checking_code = f"{akronim}-{count_akronim+1:04d}"
    generate_code = f"{akronim}-{num_kat:02d}{num_sub:02d}-{count_akronim+1:04d}"

    sequence_number = f"{tahun}{num_initial:06d}{kategori_sub_count+1:04d}"
    st.write(kategori_sub_count)
    barcode_format = barcode.get_barcode_class('code128')
    barcode_object = barcode_format(sequence_number, writer=ImageWriter())

    barcode_bytes = BytesIO()
    barcode_object.write(barcode_bytes, {"module_height": 8, "module_width": 0.3, "dpi": 200})
    barcode_bytes.seek(0)

    st.text_input("ItemCode", value=generate_code, disabled=True)
    st.text_input("Generated Description", value=generate_desc, disabled=True)
    st.text_input("Sequence Number", value=sequence_number, disabled=True)
    
    barcode_image = Image.open(barcode_bytes)
    st.image(barcode_image, width=300)
    
    if generate_desc in st.session_state.master['ItemName'].values:
        st.warning("Deskripsi sudah digunakan oleh Item Code lain.")
        st.stop()
        

    col1, col2, col3 = st.columns(3)

    if col1.button("Submit"):
        if akronim == "BELUM ADA INITIAL":
            st.warning("Belum ada Initial, silahkan reset.")
            st.stop()
        st.session_state.master = get_data("Master")
        if generate_desc in st.session_state.master['ItemName'].values:
            st.warning("Sudah disimpan, silahkan reset.")
        else:
            input_data(generate_code, generate_desc, sequence_number, kategori, subitem, checking_code)
            st.download_button(
                label="⬇ Download Barcode",
                data=barcode_bytes.getvalue(),
                file_name=f"{generate_code}.png",
                mime="image/png"
            )
            st.success("Masuk Pak Max!!!")
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    if col2.button("Reset"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

