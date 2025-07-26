import os
import pandas as pd
import requests

ARTICLES_PATH = "output/articles.csv"
FINAL_PATH = "output/final.csv"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

def gemini_translate(prompt, text):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }
    data = {
        "contents": [
            {"parts": [
                {"text": f"{prompt}\n{text}"}
            ]}
        ]
    }
    try:
        response = requests.post(GEMINI_API_URL, json=data, headers=headers, timeout=30)
        if response.status_code == 429:
            print("[Gemini] Rate limit hit, skipping this cell.")
            return None
        if response.ok:
            try:
                resp_json = response.json()
                if "candidates" in resp_json and resp_json["candidates"]:
                    parts = resp_json["candidates"][0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
                print(f"[Gemini] Unexpected response structure: {resp_json}")
                return ""
            except Exception as e:
                print(f"[Gemini] Exception extracting text: {e}")
                return ""
        print(f"[Gemini] Non-OK response: {response.status_code} {response.text}")
        return ""
    except Exception as e:
        print(f"[Gemini] Exception during request: {e}")
        return None

def main():
    # Read articles.csv
    articles = pd.read_csv(ARTICLES_PATH, dtype=str).fillna("")
    # Try to read final.csv, or create empty DataFrame if not exists
    if os.path.exists(FINAL_PATH):
        final = pd.read_csv(FINAL_PATH, dtype=str).fillna("")
    else:
        final = pd.DataFrame(columns=articles.columns.tolist() + [
            "title_eng", "content_eng",
            "title_jp", "content_jp",
            "title_cn", "content_cn",
            "title_kr", "content_kr"
        ])

    # Ensure new columns exist
    for col in [
        "title_eng", "content_eng",
        "title_jp", "content_jp",
        "title_cn", "content_cn",
        "title_kr", "content_kr"
    ]:
        if col not in final.columns:
            final[col] = ""

    # Find new rows (by url, or use another unique column if needed)
    existing_urls = set(final["url"]) if "url" in final.columns else set()
    new_rows = articles[~articles["url"].isin(existing_urls)]

    # Prepare new rows with empty translation columns
    for col in [
        "title_eng", "content_eng",
        "title_jp", "content_jp",
        "title_cn", "content_cn",
        "title_kr", "content_kr"
    ]:
        if col not in new_rows.columns:
            new_rows[col] = ""

    # Append new rows to final
    final = pd.concat([final, new_rows], ignore_index=True)

    # Fill all empty translation cells in final
    for idx, row in final.iterrows():
        # Fill title_eng if empty
        if (not row.get("title_eng")) and row.get("title"):
            prompt = "translate this tilte into English. Most importantly, only provide the pure final text as your answer, without any of your comments or unnecessary elements."
            print(f"[Gemini] Translating title for row {idx}")
            result = gemini_translate(prompt, row["title"])
            if result is not None:
                final.at[idx, "title_eng"] = result
        # Fill content_eng if empty
        if (not row.get("content_eng")) and row.get("content"):
            prompt = "translate this content into English. And then summarize the translated content into 200 words short. Most importantly, only provide the pure final text as your answer, without any of your comments or unnecessary elements."
            print(f"[Gemini] Translating content for row {idx}")
            result = gemini_translate(prompt, row["content"])
            if result is not None:
                final.at[idx, "content_eng"] = result

        # Fill new language columns from English
        for lang, lang_name in zip(["jp", "cn", "kr"], ["Japanese", "Chinese", "Korean"]):
            # Title translation
            title_col = f"title_{lang}"
            if (not row.get(title_col)) and row.get("title_eng"):
                prompt = f"translate following into {lang_name} and refine it. Most importantly, only provide the pure resulting content, without any of your comment or any signs."
                print(f"[Gemini] Translating title_eng to {lang_name} for row {idx}")
                result = gemini_translate(prompt, row["title_eng"])
                if result is not None:
                    final.at[idx, title_col] = result
            # Content translation
            content_col = f"content_{lang}"
            if (not row.get(content_col)) and row.get("content_eng"):
                prompt = f"translate following into {lang_name}, and then refine it in understandable and general manner. most importantly, only provide the pure resulting content, without any of your comment or any signs."
                print(f"[Gemini] Translating content_eng to {lang_name} for row {idx}")
                result = gemini_translate(prompt, row["content_eng"])
                if result is not None:
                    final.at[idx, content_col] = result

    # Save final.csv
    final.to_csv(FINAL_PATH, index=False)

if __name__ == "__main__":
    main()
