import pandas as pd
import requests
import time

API_KEY = "AIzaSyCDa97QG0QD53gYnPVup829IlFBP-sih_g"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def gemini_translate(text, prompt):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt}\n\n{text}"}
                ]
            }
        ]
    }
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        if response.status_code == 429:
            return ""
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return ""

df = pd.read_csv('output/articles.csv')

# Ensure the columns exist
if 'title ENG' not in df.columns:
    df['title ENG'] = ""
if 'Summary ENG' not in df.columns:
    df['Summary ENG'] = ""

# Only process rows where the output columns are empty or missing
for idx, row in df.iterrows():
    if not pd.isna(row['title']) and (pd.isna(row['title ENG']) or row['title ENG'] == ""):
        df.at[idx, 'title ENG'] = gemini_translate(
            row['title'],
            "please translate the content into English. Only give me the raw output, without your comments or other disturbing items."
        )
        time.sleep(1)  # avoid rate limit
    if not pd.isna(row['content']) and (pd.isna(row['Summary ENG']) or row['Summary ENG'] == ""):
        df.at[idx, 'Summary ENG'] = gemini_translate(
            row['content'],
            "please translate the content into English, and shorten it into roughly 150 words. Only give me the raw output, without your comments or other disturbing items."
        )
        time.sleep(1)  # avoid rate limit

df.to_csv('output/articles.csv', index=False)
