#!/usr/bin/env python3
# app.py - Versione finale con rotazione chiavi valide

import requests
import json
import time
import random
import os
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURAZIONE ====================
# SOLO LE CHIAVI CHE HANNO FUNZIONATO NEL TEST
VALID_KEYS = [
    "2UBQ8GwsajXwbXs10e72471480af4adaeb28a5a6a01ac89a7",
    "2UBQFmSYHD4NZGdb2f0eedc0e05b5de53a6746218bcdc139a",
    "2UBQLoR9eI8UsvL307891eb2aacfbb9a91978f37f010d2c29",
    "2UBTTPRPN6PFjLQdd5799398b26caf3a026c8ec3a9f9e5ad0",
]

# Aggiungi altre chiavi se vuoi testarle
# Puoi aggiungere le altre 14 qui

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

def get_cf_token(api_key):
    """Ottiene CF token con una specifica chiave"""
    bql_url = f"{BROWSERLESS_URL}?token={api_key}&stealth=true&proxy=residential&proxyCountry=it"
    
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
        
        if response.status_code == 401:
            log(f"   ⚠️ Chiave 401 (esaurita)")
            return None
        elif response.status_code != 200:
            log(f"   ❌ HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            log(f"   ❌ Errore: {data['errors'][0].get('message', 'Unknown')[:80]}")
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            log(f"   ✅ Token ottenuto! ({len(token)} caratteri)")
            return token
        else:
            log(f"   ❌ Token non risolto")
            return None
            
    except Exception as e:
        log(f"   ❌ Errore: {e}")
        return None

def register_with_token(token, username, email):
    """Registra usando il token"""
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
    session.get(REFERER_URL)
    
    response = session.post(
        "https://www.easyhits4u.com/index.cgi",
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=30
    )
    
    final_cookies = session.cookies.get_dict()
    
    if 'user_id' in final_cookies:
        log(f"   ✅ Registrazione riuscita! user_id: {final_cookies['user_id']}")
        return final_cookies
    else:
        log(f"   ❌ Registrazione fallita")
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
    log("🚀 ACCOUNT CREATOR (ROTAZIONE CHIAVI)")
    log("=" * 60)
    
    setup_output_dir()
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '1'))
    except:
        num_accounts = 1
    
    log(f"📊 Account da creare: {num_accounts}")
    log(f"🔑 Chiavi disponibili: {len(VALID_KEYS)}")
    
    success_count = 0
    key_index = 0
    
    for i in range(num_accounts):
        log(f"\n{'='*60}")
        log(f"📝 CREAZIONE ACCOUNT {i+1}/{num_accounts}")
        log(f"{'='*60}")
        
        username = generate_username()
        email = f"{username}@spaces0.com"
        
        log(f"👤 Username: {username}")
        log(f"📧 Email: {email}")
        
        # Prova con ogni chiave in rotazione
        token = None
        for attempt in range(len(VALID_KEYS)):
            api_key = VALID_KEYS[(key_index + attempt) % len(VALID_KEYS)]
            log(f"🔑 Tentativo con chiave: {api_key[:20]}...")
            
            token = get_cf_token(api_key)
            if token:
                key_index = (key_index + attempt) % len(VALID_KEYS)
                break
            time.sleep(2)
        
        if not token:
            log(f"❌ Nessuna chiave funzionante")
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
