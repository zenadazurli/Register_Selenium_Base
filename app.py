#!/usr/bin/env python3
# app.py - Versione senza turnstile_solver

import requests
import json
import time
import random
import os
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURAZIONE ====================
API_KEY = os.environ.get('BROWSERLESS_KEY', '2UBQ5qEPkTsCBv63a4077ae6c54e5490f1efd231f724e110f')
BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"
PASSWORD = os.environ.get('ACCOUNT_PASSWORD', 'Test123!@#')
OUTPUT_DIR = "/tmp/easyhits4u"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def setup_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def generate_username():
    syllables = ["ka","lo","mi","ta","ne","za","ga","ra","chi","lu","no","be","ce","re","di","sa"]
    count = random.randint(3, 5)
    return "u" + "".join(random.choice(syllables) for _ in range(count))

def get_cf_token():
    """Ottiene CF token da browserless"""
    log("🔑 Ottenimento CF token...")
    
    bql_url = f"{BROWSERLESS_URL}?token={API_KEY}&stealth=true&proxy=residential&proxyCountry=it"
    
    query = """
    mutation {
      goto(url: "https://www.easyhits4u.com/?join_popup_show=1", waitUntil: networkIdle) {
        status
      }
      solve(type: cloudflare, timeout: 45000) {
        solved
        token
      }
    }
    """
    
    try:
        response = requests.post(
            bql_url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        
        if response.status_code != 200:
            log(f"❌ Errore HTTP: {response.status_code}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            log(f"❌ Errori: {data['errors'][0].get('message')}")
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            log(f"✅ Token ottenuto! Lunghezza: {len(token)}")
            return token
        else:
            log(f"❌ Token non risolto")
            return None
            
    except Exception as e:
        log(f"❌ Errore: {e}")
        return None

def register_with_token(token, username, email):
    """Registra usando il token"""
    log(f"📝 Registrazione per {username}...")
    
    data = {
        'f': 'join',
        'a': 'join',
        'name': username,
        'email': email,
        'login': username,
        'pass': PASSWORD,
        'cpass': PASSWORD,
        'cf-turnstile-response': token
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/148.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': REFERER_URL,
    }
    
    session = requests.Session()
    
    # Ottieni cookie
    session.get(REFERER_URL)
    
    # Invia registrazione
    response = session.post(
        "https://www.easyhits4u.com/index.cgi",
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=30
    )
    
    final_cookies = session.cookies.get_dict()
    
    if 'user_id' in final_cookies:
        log(f"✅ Registrazione riuscita! user_id: {final_cookies['user_id']}")
        return final_cookies
    else:
        log(f"❌ Registrazione fallita")
        return None

def save_account(username, email, cookies):
    account_data = {
        "username": username,
        "email": email,
        "password": PASSWORD,
        "user_id": cookies.get('user_id'),
        "sesids": cookies.get('sesids'),
        "timestamp": datetime.now().isoformat()
    }
    
    accounts_file = f"{OUTPUT_DIR}/accounts.json"
    accounts = []
    if Path(accounts_file).exists():
        with open(accounts_file, "r") as f:
            try:
                accounts = json.load(f)
            except:
                accounts = []
    
    accounts.append(account_data)
    
    with open(accounts_file, "w") as f:
        json.dump(accounts, f, indent=2)
    
    with open(f"{OUTPUT_DIR}/accounts.txt", "a") as f:
        f.write(f"{email} | {PASSWORD} | user_id: {cookies.get('user_id')}\n")
    
    log(f"💾 Account salvato")

def main():
    log("=" * 60)
    log("🚀 ACCOUNT CREATOR (TOKEN + REQUESTS)")
    log("=" * 60)
    
    setup_output_dir()
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '1'))
    except:
        num_accounts = 1
    
    log(f"📊 Account da creare: {num_accounts}")
    
    success_count = 0
    
    for i in range(num_accounts):
        log(f"\n{'='*60}")
        log(f"📝 CREAZIONE ACCOUNT {i+1}/{num_accounts}")
        log(f"{'='*60}")
        
        username = generate_username()
        email = f"{username}@spaces0.com"
        
        log(f"👤 Username: {username}")
        log(f"📧 Email: {email}")
        
        # Ottieni token
        token = get_cf_token()
        if not token:
            log(f"❌ Impossibile ottenere token")
            continue
        
        # Registra
        cookies = register_with_token(token, username, email)
        
        if cookies:
            save_account(username, email, cookies)
            success_count += 1
        else:
            log(f"❌ Account {i+1} fallito")
        
        if i < num_accounts - 1:
            pause = random.randint(30, 60)
            log(f"⏸️ Pausa di {pause} secondi...")
            time.sleep(pause)
    
    log("\n" + "=" * 60)
    log(f"🏁 PROCESSO COMPLETATO!")
    log(f"✅ Account creati: {success_count}/{num_accounts}")
    log("=" * 60)

if __name__ == "__main__":
    main()
