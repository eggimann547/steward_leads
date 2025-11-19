#!/usr/bin/env python3
"""
Steward Seeker Agent — v1.2.0 (November 19, 2025)
FIXED: Only real recruitment / "how to become steward" posts
No more 27 false positives per subreddit
"""

import requests
from datetime import datetime
import sys
import os
import time

# ===================================================================
# CONFIG
# ===================================================================
GROK_KEY = "axi-your-real-key-here"          # ←←←←← YOUR KEY

SUBREDDITS = [
    "simracing",
    "simracingstewards",
    "iracing",
    "lemansultimatewec",
    "accompetizione",
    "assettocorsaevo",
    "granturismo7",
    "granturismo",
    "iracingleagues"
]

# These are the ONLY phrases that mean someone is LOOKING FOR or WANTING TO BECOME a steward
RECRUIT_PHRASES = [
    "looking for steward", "need steward", "recruiting steward",
    "wanted: steward", "seeking steward", "steward position",
    "join as steward", "volunteer steward", "race control needed",
    "how to become a steward", "want to be a steward", "start stewarding",
    "stewarding opportunity", "looking to steward"
]
# ===================================================================

def print_banner():
    print("\n" + "="*80)
    print("    STEWARD SEEKER AGENT — v1.2.0 (real leads only)")
    print(f"    {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("="*80 + "\n")

def fetch_from_one_subreddit(sub):
    url = f"https://www.reddit.com/r/{sub}/search.json"
    params = {
        "q": "steward OR stewards OR stewarding",   # broad first filter
        "sort": "new",
        "limit": 50,
        "t": "week"
    }
    headers = {"User-Agent": "steward-seeker-linux/1.2.0 (thesimracingstewards.com)"}
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            return []
        
        posts = r.json()["data"]["children"]
        real_leads = []
        
        for p in posts:
            d = p["data"]
            title = d["title"].lower()
            body  = (d.get("selftext","") or "").lower()
            combined = title + " " + body
            
            # ONLY count if one of the RECRUIT_PHRASES appears
            if any(phrase in combined for phrase in RECRUIT_PHRASES):
                real_leads.append({
                    "title": d["title"],
                    "text": d.get("selftext","")[:600],
                    "subreddit": d["subreddit"],
                    "user": d["author"],
                    "url": f"https://www.reddit.com{d['permalink']}",
                    "created": datetime.fromtimestamp(d["created_utc"]).strftime("%Y-%m-%d")
                })
        return real_leads
    except:
        return []

def get_all_leads():
    print(f"Searching {len(SUBREDDITS)} subreddits for real steward recruitment (last 7 days)...")
    all_leads = []
    for sub in SUBREDDITS:
        print(f"  → r/{sub.ljust(20)} ... ", end="")
        leads = fetch_from_one_subreddit(sub)
        all_leads.extend(leads)
        print(f"{len(leads)} real lead(s)")
        time.sleep(1.3)
    return all_leads

def get_grok_leads(raw_leads):
    if not raw_leads:
        return "No real steward recruitment posts found this week."

    text = "\n\n".join([
        f"r/{l['subreddit']} | u/{l['user']}\nTitle: {l['title']}\nText: {l['text']}\nURL: {l['url']}"
        for l in raw_leads
    ])

    url = "https://api.x.ai/v1/chat/completions"
    payload = {
        "model": "grok-3",
        "messages": [{
            "role": "user",
            "content": f"""Extract every genuine outreach lead from these posts.

Format exactly one per line:
League/Community: [name or desc] | Subreddit: r/[sub] | User: u/[username] | Need: [1-sentence] | URL: [link]

If nothing matches, reply only: "No qualified leads this week."

Posts:
{text}"""
        }],
        "temperature": 0.1,
        "max_tokens": 1000
    }
    headers = {
        "Authorization": f"Bearer {GROK_KEY}",
        "Content-Type": "application/json"
    }

    print("\nAsking Grok-3 to format the real leads...")
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=45)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"Grok error {r.status_code}"
    except Exception as e:
        return f"Grok failed: {e}"

# ===================== MAIN =====================
if __name__ == "__main__":
    if GROK_KEY == "axi-your-real-key-here":
        print("ERROR: Add your real Grok API key!")
        sys.exit(1)

    print_banner()

    raw_leads = get_all_leads()
    final_leads = get_grok_leads(raw_leads)

    filename = "steward_leads.txt"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n# Steward Seeker run — {datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(final_leads + "\n\n")

    print("\n" + "═"*80)
    print("REAL STEWARD RECRUITMENT LEADS (Last 7 Days)")
    print("═"*80)
    print(final_leads)
    print("\n" + "═"*80)
    print(f"Saved → {os.path.abspath(filename)}")
    print("═"*80)

    input("\nPress Enter to exit...")
