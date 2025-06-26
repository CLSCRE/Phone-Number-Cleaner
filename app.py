import pandas as pd
import requests
from time import sleep

# Twilio credentials (replace with fresh ones after regenerating)
account_sid = 'AC935841ebbf5ab62ca3bd70649affd9b9'
auth_token = '801b6d55a8643200a9beaaa4c4fd1841'

# Load E.164 formatted phone numbers
df = pd.read_csv('Formatted_Phone_List_For_Twilio.csv')
results = []

for phone in df['E164 Phone']:
    url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?type=carrier"
    response = requests.get(url, auth=(account_sid, auth_token))
    
    if response.status_code == 200:
        data = response.json()
        results.append({
            "Phone": phone,
            "Phone Type": data.get("carrier", {}).get("type"),
            "Carrier": data.get("carrier", {}).get("name"),
            "Ported": data.get("carrier", {}).get("ported"),
        })
    else:
        results.append({
            "Phone": phone,
            "Phone Type": None,
            "Carrier": None,
            "Ported": None,
        })
    
    sleep(0.5)  # Respect Twilio rate limits

# Save enriched results
output_df = pd.DataFrame(results)
output_df.to_csv("Twilio_Enriched_Output.csv", index=False)
print("Enrichment complete. Saved to Twilio_Enriched_Output.csv")
