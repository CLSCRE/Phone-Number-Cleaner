import streamlit as st
import pandas as pd
import requests
import time
from PIL import Image

# Twilio credentials from Streamlit secrets
ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
BASE_URL = "https://lookups.twilio.com/v2/PhoneNumbers"

def normalize_phone_number(phone):
    digits = ''.join(filter(str.isdigit, str(phone)))
    return digits if 10 <= len(digits) <= 11 else None

def enrich_number_twilio(phone):
    try:
        url = f"{BASE_URL}/{phone}"
        params = {"Type": "carrier"}
        response = requests.get(url, auth=(ACCOUNT_SID, AUTH_TOKEN), params=params)
        data = response.json()

        carrier_info = data.get("carrier", {})
        phone_type = carrier_info.get("type")
        carrier_name = carrier_info.get("name")
        ported = carrier_info.get("mobile_network_code") is not None

        working_score = "Low"
        if phone_type == "mobile":
            working_score = "High"
        elif phone_type in ["landline", "voip"]:
            working_score = "Medium"

        return {
            'Phone': phone,
            'Phone Type': phone_type,
            'Carrier': carrier_name,
            'Ported': ported,
            'Working Score': working_score
        }
    except Exception as e:
        return {'Phone': phone, 'Error': str(e)}

# Branding header with logo
st.set_page_config(page_title="CLS CRE Phone Enrichment (Twilio)", layout="wide")
logo_path = "https://clscre.com/wp-content/uploads/2023/05/CLS-CRE_logo_white.png"
st.image(logo_path, width=200)

st.subheader("📞 Phone Number Enrichment Tool (Twilio Lookup)")
st.caption("Upload a spreadsheet of phone numbers to identify type, carrier, and working probability using Twilio.")

uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    phone_columns = [col for col in df.columns if 'phone' in col.lower()]

    if not phone_columns:
        st.warning("No phone number columns detected.")
    else:
        st.success(f"Found phone columns: {', '.join(phone_columns)}")
        raw_phones = df[phone_columns].values.flatten()
        normalized = pd.Series(raw_phones).dropna().map(normalize_phone_number).dropna().drop_duplicates()

        st.write(f"Processing {len(normalized)} unique phone numbers...")

        enriched_data = []
        progress = st.progress(0)
        for i, phone in enumerate(normalized):
            enriched_data.append(enrich_number_twilio(phone))
            progress.progress((i + 1) / len(normalized))
            time.sleep(1)

        result_df = pd.DataFrame(enriched_data)
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Enriched Results as CSV",
            data=csv,
            file_name="twilio_enriched_phone_numbers.csv",
            mime='text/csv'
        )
