import os
import pandas as pd
import requests

ARTICLES_PATH = "output/articles.csv"
FINAL_PATH = "output/final.csv"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY

def gemini_translate(prompt, text):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt.replace("{text}", text)}]}
        ]
    }
    response = requests.post(GEMINI_API_URL, json=data, headers=headers)
    if response.ok:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            return ""
    return ""

def main():
    # Read articles.csv
    articles = pd.read_csv(ARTICLES_PATH, dtype=str).fillna("")
    # Try to read final.csv, or create empty DataFrame if not exists
    if os.path.exists(FINAL_PATH):
        final = pd.read_csv(FINAL_PATH, dtype=str).fillna("")
    else:
        final = pd.DataFrame(columns=articles.columns.tolist() + ["title_eng", "content_eng"])

    # Ensure new columns exist
    for col in ["title_eng", "content_eng"]:
        if col not in final.columns:
            final[col] = ""

    # Find new rows (by url, or use another unique column if needed)
    existing_urls = set(final["url"]) if "url" in final.columns else set()
    new_rows = articles[~articles["url"].isin(existing_urls)]

    # Prepare new rows with empty translation columns
    for col in ["title_eng", "content_eng"]:
        if col not in new_rows.columns:
            new_rows[col] = ""

    # Translate missing title_eng/content_eng
    for idx, row in new_rows.iterrows():
        if not row.get("title_eng"):
            prompt = "translate this tilte into English. Most importantly, only provide the pure final text as your answer, without any of your comments or unnecessary elements."
            final_title = gemini_translate(prompt, row["title"])
            new_rows.at[idx, "title_eng"] = final_title
        if not row.get("content_eng"):
            prompt = "translate this content into English. And then summarize the translated content into 200 words short. Most importantly, only provide the pure final text as your answer, without any of your comments or unnecessary elements."
            final_content = gemini_translate(prompt, row["content"])
            new_rows.at[idx, "content_eng"] = final_content

    # Append new rows to final
    final = pd.concat([final, new_rows], ignore_index=True)
    # Save final.csv
    final.to_csv(FINAL_PATH, index=False)

if __name__ == "__main__":
    main()
