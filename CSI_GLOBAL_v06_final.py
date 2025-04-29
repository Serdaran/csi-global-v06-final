
import streamlit as st
import pandas as pd
#import os
#from dotenv import load_dotenv
from google.oauth2 import service_account
import gspread
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

def upload_file_to_drive(uploaded_file, credentials):
   
    service = build('drive', 'v3', credentials=credentials)

    file_metadata = {
        'name': uploaded_file.name,
        'parents': []  # Eğer Drive içinde bir klasöre atılacaksa burada klasör ID verilebilir.
    }
    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)

    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    file_id = file.get('id')
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    public_url = f"https://drive.google.com/uc?id={file_id}"
    return public_url

# .env dosyasını yükle
load_dotenv()

# Google Drive kimlik bilgilerini oku
from google.oauth2.service_account import Credentials


scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_file('service_account_key.json', scopes=scopes)


gc = gspread.authorize(credentials)


st.set_page_config(page_title="CSI:GLOBAL - Uç Aşınma Veri Girişi", layout="centered")
st.title("CSI:GLOBAL - Uç Aşınma Analiz Formu (Wear Analysis Form)")

# Form başlıyor
with st.form("wear_form"):
    st.subheader("Uç Bilgileri (Tool Information)")

    customer_name = st.text_input("Müşteri Adı (Customer Name)")

    tool_code = st.text_input("1. Uç ISO Kodu (Tool ISO Code)")
    chipbreaker = st.text_input("3. Talaş Kırıcı (Chipbreaker)")
    tool_grade = st.text_input("2. Kalite Kodu (Grade Code)")
    
    st.subheader("İşleme Parametreleri (Machining Parameters)")

    material_options = [
    "P-01_Alaşımsız Çelik (Unalloyed Steel) | HB110 | C15 ; C45 ; C60",
    "P-02_Düşük Alaşımlı Çelik (Low Alloyed Steel) | HB180 | 21NiCrMo2 ; 36CrNiMo4 ; 34CrMo4",
    "P-03_Yüksek Alaşımlı Çelik (High Alloyed Steel) | HB200 | 34CrNiMo6 ; 42CrMo4",
    "P-04_Yüksek Alaşımlı Çelik (High Alloyed Steel) | HB400 | X40CrMoV5 ; X45GrSi93",
    "M-01_Ferritik/Martensitik Paslanmaz Çelik (Ferritic/Martensitic Stainless Steel) | X12CrMoS17 ; X6CrMo17",
    "M-02_Östenitik Paslanmaz Çelik (Austenitic Stainless Steel) | X5CrNi189 ; X5CrNiMo18 ; X15CrNiSi20",
    "M-03_Duplex Paslanmaz Çelik (Duplex Stainless Steel) | X2CrNiMoSi19 ; X8CrNiMo27 ; X2CrNiMoN22",
    "K-01_Gri Dökme Demir (Grey Cast Iron) | HB220 | GG15 ; GG25 ; GG35",
    "K-02_Sfero Dökme Demir (Nodular Cast Iron) | HB180 | GGG40 ; GGG50 ; GGG70",
    "S-01_Titanyum Alaşımları (Titanium Alloys) | TiAl5Sn2.5 ; TiAl6V4 ; TiAl6V4ELI",
    "S-02_Titanyum Alaşımları (Titanium Alloys) | NiCr19Co11MoTi ; NiFe35Cr14MoTi ; CoCr20W15Ni ; Inconel",
    "N-01_Alüminyum Alaşımları (Aluminium Alloys) | AW7075 ; AlSi12 ; CuZn37",
    "H-01_Sertleştirilmiş Çelikler (Hardened Steels) | 50-60 HRc"
    ]

    
    material = st.selectbox("4. İşlenen Malzeme (Workpiece Material)", material_options)

   
    cutting_speed = st.number_input("5. Kesme Hızı (Cutting Speed) [m/min]", min_value=0.0, step=0.1)
    feed_rate = st.number_input("6. İlerleme (Feed per Revolution) [mm/rev]", min_value=0.0, step=0.01)
    depth_of_cut = st.number_input("7. Talaş Derinliği (Depth of Cut) [mm]", min_value=0.0, step=0.1)

    st.subheader("Görseller (Images)")

    tool_image = st.file_uploader("8. Uç Görseli Yükle (Upload Tool Image)", type=["jpg", "jpeg", "png"])
    chip_image = st.file_uploader("9. Opsiyonel: Talaş Görseli Yükle (Upload Chip Image)", type=["jpg", "jpeg", "png"])

    submit = st.form_submit_button("Kaydet (Save)")

if submit:
    st.success("✅ Veriniz başarıyla kaydedildi! (Your data has been saved!)")

    sh = gc.open("CSI_GLOBAL_DATA")
    

    try:
        worksheet = sh.worksheet("Wear_Records")
    except:
        worksheet = sh.add_worksheet(title="Wear_Records", rows="1000", cols="20")
    
    if tool_image is not None:
        tool_image_link = upload_file_to_drive(tool_image, credentials)
    else:
        tool_image_link = ""

    if chip_image is not None:
        chip_image_link = upload_file_to_drive(chip_image, credentials)
    else:
        chip_image_link = ""

    new_row = [
        customer_name,
        material,
        cutting_speed,
        feed_rate,
        depth_of_cut,
        tool_image_link,
        chip_image_link
    ]

    #worksheet.append_row(new_row)

    # Basit Aşınma Analiz Algoritması
    if cutting_speed > 200:
        wear_type = "Crater Wear (Krater Aşınması)"
        advice = "Kesme hızınızı %10 azaltın."
    elif feed_rate > 0.3:
        wear_type = "Flank Wear (Yanak Aşınması)"
        advice = "İlerlemenizi %10 azaltın."
    elif depth_of_cut > 2:
        wear_type = "Notching (Çentik Aşınması)"
        advice = "Talaş derinliğini azaltın."
    else:
        wear_type = "Hafif Flank Wear (Light Flank Wear)"
        advice = "Parametreleriniz uygun görünüyor."

    st.info(f"🔍 Tahmini Aşınma Tipiniz (Estimated Wear Type): **{wear_type}**")
    st.warning(f"💡 Tavsiye (Suggestion): {advice}")

    # Verileri CSV'ye kaydet
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_data = pd.DataFrame({
        "timestamp": [timestamp],
        "customer_name": [customer_name],
        "tool_code": [tool_code],
        "chipbreaker": [chipbreaker],
        "tool_grade": [tool_grade],
        "material": [material],
        "cutting_speed": [cutting_speed],
        "feed_rate": [feed_rate],
        "depth_of_cut": [depth_of_cut],
        "wear_type_estimation": [wear_type],
        "advice_given": [advice],
        "tool_image_link": [tool_image_link],
        "chip_image_link": [chip_image_link]
    })

   
    existing_data = pd.DataFrame(worksheet.get_all_records())
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    updated_data = updated_data.fillna("")
    #worksheet.clear()
    worksheet.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())
