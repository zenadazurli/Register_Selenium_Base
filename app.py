#!/usr/bin/env python3
# app.py - Versione con timeout 10 minuti e polling migliorato

import requests
import json
import time
import random
import re
import os
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURAZIONE ====================
VALID_KEYS = [
    "2UBnPb0EAl96VbQ6adf224ec4c56e12bb19959eea41b57455",
    "2UBQ8GwsajXwbXs10e72471480af4adaeb28a5a6a01ac89a7",
    "2UBQFmSYHD4NZGdb2f0eedc0e05b5de53a6746218bcdc139a",
    "2UBQLoR9eI8UsvL307891eb2aacfbb9a91978f37f010d2c29",
    "2UBTTPRPN6PFjLQdd5799398b26caf3a026c8ec3a9f9e5ad0",
    "2UBnDTit4q9XEKDc5dd928eaaeeba1e19355f5790e6448609",
    "2UBnGaSy3OUY3GQ62740ff8c64d0d4e59234618332e5879f6",
    "2UBnL3CDkxjWE7Ef9fd7a3754e753f4a7df4a582343e67189",
    "2UBnUJVWwcmHbaH321b18bc4fa5cb527ff4bae25b410ea79b",
    "2UBnajgrly8o8M366e5539887aed33147fc9e7d6adbffde28",
    "2UBnenIqwlRCGjT61471ba64e010b673df4b93449efd24494",
    "2UBniEYYrZzpzdDf30240c479a5f85cfe9221f154adac46f6",
    "2UBnpegeItTC8i4a087228298c4fc589dc969a00d3c86baef",
    "2UBntqTS8E2iYAca48bfa4bdb4a59a46c00767670378c200b",
    "2UBoxxfROlib6N3bfe56f7ea2402f355a47734ad544c2d273",
    "2UBp2zjSczUb9pK6bc8cadbafaa6c5145b82bcc4b765ff969",
    "2UBpKxZ0VgVIu1zf279654e8504f7248833d1640727e0805d",
    "2UBpOkJdxpfndxpc117cd35c83a5437b126f188e0859939b2",
    "2UBpUGukRq5oz4U504e5e0c0a5dfaad68bf265f49874a4bcd",
    "2UBpYiQZStmFIEB262f92847d674e3c606d7b3112cee932bc",
    "2UBpgTLTEKG9IlFc5423ccd37cb069c09c5b4d002f97bb88f",
    "2UBpkU9rUMQJelq3695f9c9f96e25aa4f19dad3ced3167776",
    "2UBpsO76fPFcEHNdf43337716ff8d08bf50f9f41706b6b9f0",
    "2UBpzRVHmDEMJszf1f584b4cf666130d2ec02f8c2c5cee474",
]

BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"
OUTPUT_DIR = "/tmp/easyhits4u"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"

MAX_ACCOUNTS_PER_IP = 3
accounts_created = 0
current_ip_session = None

MAIL_EMAIL = "paolocrescentini@dollicons.com"
MAIL_PASSWORD = "HG65$!dava"
MAIL_BASE_URL = "https://api.mail.tm"

# ==================== STATISTICHE ====================
stats = {
    "total_attempts": 0,
    "successful_registrations": 0,
    "successful_activations": 0,
    "ip_changes": 0,
    "keys_used": {}
}

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def setup_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def load_register_config():
    config_path = Path("register_config.json")
    if not config_path.exists():
        raise FileNotFoundError("❌ register_config.json mancante")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["email_local"], data["email_domain"], data["password"]

def generate_username():
    syllables = ["ka","lo","mi","ta","ne","za","ga","ra","chi","lu","no","be","ce","re","di","sa"]
    count = random.randint(3, 5)
    return "u" + "".join(random.choice(syllables) for _ in range(count))

def build_email(username, email_local, email_domain):
    return f"{email_local}+{username}@{email_domain}"

def get_new_ip_session():
    global current_ip_session, accounts_created, stats
    current_ip_session = f"{int(time.time())}_{random.randint(1000, 9999)}"
    accounts_created = 0
    stats["ip_changes"] += 1
    log(f"🔄 NUOVO IP: Sessione {current_ip_session} (cambio #{stats['ip_changes']})")
    return current_ip_session

def get_browserless_url(api_key):
    global current_ip_session, accounts_created
    if current_ip_session is None or accounts_created >= MAX_ACCOUNTS_PER_IP:
        get_new_ip_session()
    return f"{BROWSERLESS_URL}?token={api_key}&stealth=true&proxy=residential&proxyCountry=it&session={current_ip_session}"

def get_cf_token(api_key):
    global accounts_created, stats
    
    bql_url = get_browserless_url(api_key)
    log(f"   🌐 Sessione: {current_ip_session} | Account {accounts_created+1}/{MAX_ACCOUNTS_PER_IP}")
    
    query = """
    mutation {
      goto(url: "https://www.easyhits4u.com/?join_popup_show=1", waitUntil: networkIdle, timeout: 60000) {
        status
      }
      solve(type: cloudflare, timeout: 60000) {
        solved
        token
        time
      }
    }
    """
    
    try:
        start_time = time.time()
        response = requests.post(bql_url, json={"query": query}, headers={"Content-Type": "application/json"}, timeout=120)
        elapsed = time.time() - start_time
        
        if response.status_code == 401:
            return None
        elif response.status_code != 200:
            return None
        
        data = response.json()
        if "errors" in data:
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            log(f"   ✅ Token ottenuto! ({len(token)} char, {elapsed:.1f}s)")
            accounts_created += 1
            return token
        return None
    except:
        return None

def register_with_token(token, username, email, password):
    data = {
        'f': 'join', 'a': 'join', 'name': username, 'email': email,
        'login': username, 'pass': password, 'cpass': password,
        'cf-turnstile-response': token
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/148.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': REFERER_URL,
    }
    
    session = requests.Session()
    session.get(REFERER_URL)
    
    response = session.post("https://www.easyhits4u.com/index.cgi", data=data, headers=headers, allow_redirects=True, timeout=30)
    final_cookies = session.cookies.get_dict()
    
    if 'user_id' in final_cookies:
        log(f"   ✅ Registrazione OK! user_id: {final_cookies['user_id']}")
        stats["successful_registrations"] += 1
        return final_cookies
    return None

class MailTMActivator:
    def __init__(self):
        self.session = requests.Session()
        self.last_processed_id = None
        self.target_email = None
        
    def login(self):
        try:
            log("🔐 Login Mail.tm...")
            res = self.session.post(f"{MAIL_BASE_URL}/token", json={"address": MAIL_EMAIL, "password": MAIL_PASSWORD})
            if res.status_code != 200:
                raise Exception(f"Login fallito: {res.status_code}")
            token = res.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            log("✅ Login Mail.tm OK")
            return True
        except Exception as e:
            log(f"❌ Errore login Mail.tm: {e}")
            return False
    
    def set_target_email(self, email):
        self.target_email = email.lower()
    
    def get_all_messages(self):
        try:
            res = self.session.get(f"{MAIL_BASE_URL}/messages")
            if res.status_code == 200:
                return res.json().get("hydra:member", [])
        except:
            pass
        return []
    
    def get_activation_email(self):
        try:
            messages = self.get_all_messages()
            for msg in messages:
                try:
                    # Controlla destinatario
                    to_emails = []
                    for recipient in msg.get("to", []):
                        if isinstance(recipient, dict):
                            to_emails.append(recipient.get("address", "").lower())
                        elif isinstance(recipient, str):
                            to_emails.append(recipient.lower())
                    
                    if self.target_email not in str(to_emails):
                        continue
                        
                    subject = msg.get("subject", "").lower()
                    if "activate your easyhits4u account" in subject:
                        return msg
                except:
                    continue
        except:
            pass
        return None
    
    def extract_activation_link(self, text):
        try:
            patterns = [
                r'(https?://)?www\.easyhits4u\.com/\?emlac=[^\s\]"\']+',
                r'href=["\'](https?://www\.easyhits4u\.com/\?emlac=[^"\']+)["\']',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    link = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    if not link.startswith("http"):
                        link = "https://" + link
                    return link
        except:
            pass
        return None
    
    def activate_account(self, link):
        try:
            log(f"🔗 Apertura link attivazione...")
            r = requests.get(link, timeout=15, allow_redirects=True)
            final_url = r.url
            if "email_ok" in final_url or "mail_activated" in final_url:
                log(f"✅ Attivazione completata!")
                return True
            return False
        except:
            return False
    
    def wait_for_activation(self, timeout_minuti=10):
        log(f"📧 Attesa email per {self.target_email}...")
        log(f"   Timeout: {timeout_minuti} minuti")
        
        # Mostra email presenti
        try:
            messages = self.get_all_messages()
            log(f"📨 Email nella inbox: {len(messages)}")
            for i, msg in enumerate(messages[:3]):
                to_addr = msg.get("to", [{}])[0].get("address", "N/A") if msg.get("to") else "N/A"
                log(f"   {i+1}. {msg.get('subject', 'N/A')[:40]} -> {to_addr}")
        except:
            pass
        
        start = time.time()
        last_log_time = 0
        
        while time.time() - start < timeout_minuti * 60:
            elapsed = int(time.time() - start)
            
            # Log ogni 60 secondi
            if elapsed - last_log_time >= 60:
                log(f"⏳ Attesa email... ({elapsed}s / {timeout_minuti*60}s)")
                last_log_time = elapsed
            
            try:
                message = self.get_activation_email()
                
                if message:
                    msg_id = message["id"]
                    if msg_id == self.last_processed_id:
                        time.sleep(5)
                        continue
                    
                    log(f"📧 EMAIL TROVATA! (dopo {elapsed}s)")
                    log(f"   Oggetto: {message['subject']}")
                    
                    res = self.session.get(f"{MAIL_BASE_URL}/messages/{msg_id}")
                    if res.status_code != 200:
                        time.sleep(5)
                        continue
                        
                    msg_data = res.json()
                    body = msg_data.get("text") or msg_data.get("html", "")
                    link = self.extract_activation_link(body)
                    
                    if link:
                        self.last_processed_id = msg_id
                        success = self.activate_account(link)
                        return success
            except:
                pass
            
            time.sleep(5)
        
        log(f"❌ Timeout attivazione dopo {timeout_minuti} minuti")
        return False

def save_account(username, email, password, cookies, activated=False):
    status = "✅ ATTIVATO" if activated else "⏳ IN ATTESA"
    with open(f"{OUTPUT_DIR}/accounts.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}    Password {password}    [{status}]    user_id:{cookies.get('user_id', 'N/A')}\n")
    log(f"💾 Account salvato: {email} [{status}]")
    if activated:
        stats["successful_activations"] += 1

def main():
    global accounts_created, current_ip_session, stats
    
    log("=" * 70)
    log("🚀 EASYHITS4U ACCOUNT CREATOR v5.0")
    log("=" * 70)
    log(f"🔑 API key: {len(VALID_KEYS)}")
    log(f"⚠️ Max {MAX_ACCOUNTS_PER_IP} account per IP")
    log(f"📧 Timeout attivazione: 10 minuti")
    log("=" * 70)
    
    setup_output_dir()
    
    try:
        email_local, email_domain, default_password = load_register_config()
        log(f"📁 Config: {email_local}@{email_domain}")
    except FileNotFoundError as e:
        log(f"❌ {e}")
        return
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '3'))
    except:
        num_accounts = 3
    
    log(f"📊 Account da creare: {num_accounts}")
    
    mail_activator = MailTMActivator()
    if not mail_activator.login():
        return
    
    success_count = 0
    key_index = 0
    
    for i in range(num_accounts):
        log(f"\n{'='*70}")
        log(f"📝 ACCOUNT {i+1}/{num_accounts}")
        log(f"{'='*70}")
        
        username = generate_username()
        email = build_email(username, email_local, email_domain)
        
        log(f"👤 {username}")
        log(f"📧 {email}")
        
        # Ottieni token
        token = None
        for attempt in range(len(VALID_KEYS)):
            api_key = VALID_KEYS[(key_index + attempt) % len(VALID_KEYS)]
            token = get_cf_token(api_key)
            if token:
                key_index = (key_index + attempt) % len(VALID_KEYS)
                break
            time.sleep(1)
        
        if not token:
            log(f"❌ Nessuna chiave funzionante")
            continue
        
        # Registra
        cookies = register_with_token(token, username, email, default_password)
        if not cookies:
            continue
        
        # Attiva
        mail_activator.set_target_email(email)
        activated = mail_activator.wait_for_activation(timeout_minuti=10)
        
        # Salva
        save_account(username, email, default_password, cookies, activated)
        
        if activated:
            success_count += 1
            log(f"🎉 Account {i+1} COMPLETATO!")
        else:
            log(f"⚠️ Account {i+1} creato ma NON attivato")
        
        if i < num_accounts - 1:
            pause = random.randint(30, 60)
            log(f"⏸️ Pausa {pause}s...")
            time.sleep(pause)
    
    log("\n" + "=" * 70)
    log(f"🏁 COMPLETATO! ✅ {success_count}/{num_accounts} account attivati")
    log(f"📁 Output: {OUTPUT_DIR}/accounts.txt")
    log("=" * 70)

if __name__ == "__main__":
    main()
