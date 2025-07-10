import pandas as pd
import requests
import time

API_KEY = "AIzaSyCDa97QG0QD53gYnPVup829IlFBP-sih_g"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + API_KEY

def gemini_translate(text, prompt):
    headers = {"Content-Type": "application/json"}
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

df = pd.read_csv('output/articles.csv', sep='\t')  # adjust sep if needed

# Translate titles
df['title ENG'] = df['title'].apply(lambda x: gemini_translate(
    x, "please translate the content into English. Only give me the raw output, without your comments or other disturbing items."))

# Translate and summarize content
df['Summary ENG'] = df['content'].apply(lambda x: gemini_translate(
    x, "please translate the content into English, and shorten it into roughly 150 words. Only give me the raw output, without your comments or other disturbing items."))

df.to_csv('output/articles.csv', sep='\t', index=False)
