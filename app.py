
import pandas as pd
import streamlit as st
import requests
from time import sleep

def format_to_e164(phone):
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 10:
        return "+1" + phone
    elif len(phone) == 11 and phone.startswith("1"):
        return "+" + phone
    elif phone.startswith("+") and len(phone) > 10:
        return phone
    return None

def lookup_status(phone, sid, token):
    if not phone or not phone.startswith("+"):
        return ("", "", "", "", "", phone, "Invalid")

    url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?Type=carrier"
    try:
        response = requests.get(url, auth=(sid, token))
        if response.status_code == 200:
            data = response.json()
            phone_type = data.get("carrier", {}).get("type", "")
            carrier = data.get("carrier", {}).get("name", "")
            ported = data.get("carrier", {}).get("ported", "")
            country = data.get("country_code", "")
            national_format = data.get("national_format", "")
            return (phone_type, carrier, ported, country, national_format, phone, "Valid")
    except Exception as e:
        print(f"Lookup failed for {phone}: {e}")
    return ("", "", "", "", "", phone, "Error")

st.title("📞 Multi-Column Phone Extractor & Twilio Enricher")

uploaded_file = st.file_uploader("Upload Excel File with Phone Numbers", type=["xlsx"])
account_sid = st.text_input("🔐 Twilio Account SID")
auth_token = st.text_input("🔑 Twilio Auth Token", type="password")

if uploaded_file and account_sid and auth_token:
    df = pd.read_excel(uploaded_file)
    phone_cols = [col for col in df.columns if 'phone' in col.lower()]
    if not phone_cols:
        st.error("No phone-related columns found.")
        st.stop()

    st.success(f"Found phone columns: {phone_cols}")

    cleaned_df = df.copy()
    for col in phone_cols:
        cleaned_df[col] = cleaned_df[col].astype(str).apply(format_to_e164)

    phone_list = [cleaned_df[col] for col in phone_cols]
    phone_series = pd.concat(phone_list, ignore_index=True).dropna().drop_duplicates().reset_index(drop=True)

    enriched_df = pd.DataFrame({'Phone': phone_series})
    enriched_df[[
        'Phone Type', 'Carrier', 'Ported', 'Country',
        'National Format', 'E.164 Phone', 'Status'
    ]] = enriched_df['Phone'].apply(
        lambda x: pd.Series(lookup_status(x, account_sid, auth_token))
    )

    st.write("✅ Twilio Enriched Preview")
    st.dataframe(enriched_df.head(25))

    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        cleaned_df.to_excel(writer, index=False, sheet_name='Cleaned Phone Sheet')
        enriched_df.to_excel(writer, index=False, sheet_name='Twilio Enriched')
    st.download_button("📥 Download Enriched Excel", output.getvalue(), file_name="twilio_enriched_output.xlsx")
