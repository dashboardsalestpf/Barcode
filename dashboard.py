import streamlit as st
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import gspread
from datetime import datetime
from io import BytesIO
import pandas as pd
from google.oauth2 import service_account
import zipfile

# Streamlit Title
st.title("Barcode Generator")

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
with st.spinner("Updating Master Data . . . "):
    st.session_state.master = get_data("Master")
# Load Data into Session State

    
        

st.dataframe(st.session_state.master)

# Multiselect ItemCode
itemcodes = st.multiselect("Select ItemCode", st.session_state.master["ItemCode"].unique())

# Button to Generate Barcode
if st.button("Generate Barcode"):
    if not itemcodes:
        st.warning("Please select at least one ItemCode.")
    else:
        zip_buffer = BytesIO()
        sample_image = None  # Variabel untuk menyimpan sample barcode
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for idx, itemcode in enumerate(itemcodes):
                # Cari SequenceNumber berdasarkan ItemCode
                seq_number = st.session_state.master.loc[
                    st.session_state.master["ItemCode"] == itemcode, "SequenceNumber"
                ].values
                
                if len(seq_number) == 0:
                    continue  # Skip jika tidak ada SequenceNumber

                seq_number = str(seq_number[0])  # Konversi ke string

                barcode_class = barcode.get_barcode_class("code128")
                barcode_obj = barcode_class(seq_number, writer=ImageWriter())

                img_buffer = BytesIO()
                barcode_obj.write(img_buffer)
                img_buffer.seek(0)

                zip_file.writestr(f"{itemcode}.png", img_buffer.read())
                
                # Simpan sample barcode hanya untuk item pertama
                if idx == 0:
                    img_buffer.seek(0)
                    sample_image = Image.open(img_buffer)

        zip_buffer.seek(0)
        
        # Tampilkan sample barcode di Streamlit jika ada
        if sample_image:
            st.image(sample_image, caption=f"Sample Barcode for {itemcodes[0]}", use_column_width=True)
        
        # Auto download zip file
        st.download_button("Download Barcode", zip_buffer, "barcodes.zip", "application/zip")
