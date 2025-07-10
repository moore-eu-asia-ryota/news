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
    response = requests.post(API_URL, json=data, headers=headers)
    response.raise_for_status()
    return response.json()['candidates'][0]['content']['parts'][0]['text']

# Read the CSV (comma-separated, with clean headers)
df = pd.read_csv('output/articles.csv')

# Translate titles to English
df['title ENG'] = df['title'].apply(lambda x: gemini_translate(
    x, "please translate the content into English. Only give me the raw output, without your comments or other disturbing items."))

# Translate and summarize content to English (~150 words)
df['Summary ENG'] = df['content'].apply(lambda x: gemini_translate(
    x, "please translate the content into English, and shorten it into roughly 150 words. Only give me the raw output, without your comments or other disturbing items."))

# Save the updated CSV
df.to_csv('output/articles.csv', index=False)
