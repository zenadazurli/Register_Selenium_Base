#!/usr/bin/env python3
# app.py - Versione con rotazione IP (max 3 account per IP)

import requests
import json
import time
import random
import re
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

# ==================== CONFIGURAZIONE ====================
VALID_KEYS = [
    "2UBQ8GwsajXwbXs10e72471480af4adaeb28a5a6a01ac89a7",
    "2UBQFmSYHD4NZGdb2f0eedc0e05b5de53a6746218bcdc139a",
    "2UBQLoR9eI8UsvL307891eb2aacfbb9a91978f37f010d2c29",
    "2UBTTPRPN6PFjLQdd5799398b26caf3a026c8ec3a9f9e5ad0",
]

BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"
OUTPUT_DIR = "/tmp/easyhits4u"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"

# ==================== LIMITI IP ====================
MAX_ACCOUNTS_PER_IP = 3
accounts_on_current_ip = 0
current_session_id = None

# ==================== MAIL.TM CONFIG ====================
MAIL_EMAIL = "paolocrescentini@dollicons.com"
MAIL_PASSWORD = "HG65$!dava"
MAIL_BASE_URL = "https://api.mail.tm"

# ==================== FUNZIONI UTILITY ====================
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def setup_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def load_register_config():
    """Carica la configurazione da register_config.json"""
    config_path = Path("register_config.json")
    if not config_path.exists():
        raise FileNotFoundError("❌ register_config.json mancante")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data["email_local"], data["email_domain"], data["password"]

def generate_username():
    """Genera username casuale"""
    syllables = ["ka","lo","mi","ta","ne","za","ga","ra","chi","lu","no","be","ce","re","di","sa"]
    count = random.randint(3, 5)
    return "u" + "".join(random.choice(syllables) for _ in range(count))

def build_email(username, email_local, email_domain):
    """Costruisce email nel formato: email_local+username@email_domain"""
    return f"{email_local}+{username}@{email_domain}"

def get_next_session_id():
    """Genera un nuovo ID sessione per il cambio IP"""
    global current_session_id, accounts_on_current_ip
    current_session_id = random.randint(10000, 99999)
    accounts_on_current_ip = 0
    log(f"🔄 Nuova sessione IP: {current_session_id}")
    return current_session_id

def get_browserless_url_with_session(api_key):
    """Costruisce URL con session ID per cambio IP"""
    global current_session_id, accounts_on_current_ip
    
    if current_session_id is None or accounts_on_current_ip >= MAX_ACCOUNTS_PER_IP:
        get_next_session_id()
    
    # Aggiungi session param per cambiare IP
    session_param = f"&session={current_session_id}"
    bql_url = f"{BROWSERLESS_URL}?token={api_key}&stealth=true&proxy=residential&proxyCountry=it{session_param}"
    
    return bql_url

def get_cf_token(api_key):
    """Ottiene CF token con rotazione IP automatica"""
    global accounts_on_current_ip
    
    bql_url = get_browserless_url_with_session(api_key)
    log(f"   Session IP: {current_session_id} (account {accounts_on_current_ip+1}/{MAX_ACCOUNTS_PER_IP})")
    
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
            return None
        elif response.status_code != 200:
            return None
        
        data = response.json()
        
        if "errors" in data:
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            # Incrementa contatore account su questo IP
            accounts_on_current_ip += 1
            return token
        return None
            
    except Exception:
        return None

def register_with_token(token, username, email, password):
    """Registra usando il token"""
    data = {
        'f': 'join',
        'a': 'join',
        'name': username,
        'email': email,
        'login': username,
        'pass': password,
        'cpass': password,
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
        return final_cookies
    return None

# ==================== MAIL.TM CLASS ====================
class MailTMActivator:
    def __init__(self):
        self.session = requests.Session()
        self.last_processed_id = None
        self.target_email = None
        
    def login(self):
        try:
            log("🔐 Login a Mail.tm...")
            res = self.session.post(
                f"{MAIL_BASE_URL}/token",
                json={"address": MAIL_EMAIL, "password": MAIL_PASSWORD}
            )
            if res.status_code != 200:
                raise Exception(f"Login fallito: {res.status_code}")
            token = res.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            log("✅ Login Mail.tm completato")
            return True
        except Exception as e:
            log(f"❌ Errore login Mail.tm: {e}")
            return False
    
    def set_target_email(self, email):
        self.target_email = email.lower()
        
    def get_activation_email(self):
        try:
            res = self.session.get(f"{MAIL_BASE_URL}/messages")
            if res.status_code != 200:
                return None
            messages = res.json().get("hydra:member", [])
            
            for msg in messages:
                try:
                    to_email = msg.get("to", [{}])[0].get("address", "").lower()
                    if self.target_email and self.target_email not in to_email:
                        continue
                        
                    subject = msg.get("subject", "").lower()
                    sender = msg.get("from", {}).get("address", "").lower()
                    
                    if ("activate your easyhits4u account" in subject or 
                        "support@easyhits4u.com" in sender):
                        return msg
                except:
                    continue
        except Exception as e:
            log(f"⚠️ Errore recupero email: {e}")
        return None
    
    def extract_activation_link(self, text):
        try:
            match = re.search(
                r'(https?://)?www\.easyhits4u\.com/\?emlac=[^\s\]"]+',
                text
            )
            if match:
                link = match.group(0)
                if not link.startswith("http"):
                    link = "https://" + link
                return link
        except Exception as e:
            log(f"⚠️ Errore estrazione link: {e}")
        return None
    
    def activate_account(self, link):
        log(f"🔄 Attivazione account...")
        try:
            r = requests.get(link, timeout=15, allow_redirects=True)
            final_url = r.url
            if "email_ok" in final_url or "mail_activated" in final_url:
                log(f"✅ Attivazione completata!")
                return True
            else:
                log(f"⚠️ Attivazione fallita: status {r.status_code}")
                return False
        except Exception as e:
            log(f"❌ Errore attivazione: {e}")
            return False
    
    def wait_for_activation(self, timeout_minuti=3):
        log(f"📧 In attesa email di attivazione per {self.target_email}...")
        start = time.time()
        
        while time.time() - start < timeout_minuti * 60:
            try:
                message = self.get_activation_email()
                if message:
                    msg_id = message["id"]
                    
                    if msg_id == self.last_processed_id:
                        time.sleep(5)
                        continue
                    
                    log(f"📧 Email trovata! Oggetto: {message['subject']}")
                    
                    res = self.session.get(f"{MAIL_BASE_URL}/messages/{msg_id}")
                    if res.status_code != 200:
                        time.sleep(5)
                        continue
                        
                    msg_data = res.json()
                    
                    body = msg_data.get("text") or msg_data.get("html", "")
                    link = self.extract_activation_link(body)
                    
                    if link:
                        log(f"🔗 Link di attivazione trovato")
                        self.last_processed_id = msg_id
                        
                        success = self.activate_account(link)
                        return success
                    else:
                        log("⚠️ Link non trovato nel messaggio")
                        
                time.sleep(5)
                
            except Exception as e:
                log(f"⚠️ Errore durante polling: {e}")
                time.sleep(5)
        
        log("❌ Timeout: email di attivazione non arrivata")
        return False

# ==================== SALVATAGGIO ====================
def save_account(username, email, password, cookies, activated=False):
    """Salva account in formato leggibile"""
    account_data = {
        "username": username,
        "email": email,
        "password": password,
        "user_id": cookies.get('user_id'),
        "sesids": cookies.get('sesids'),
        "activated": activated,
        "session_ip": current_session_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Salva in JSON
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
    
    # Salva in TXT
    status = "ATTIVATO" if activated else "IN ATTESA"
    with open(f"{OUTPUT_DIR}/accounts.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}    Password {password}    [{status}]    IP: {current_session_id}\n")
    
    log(f"💾 Account salvato: {email}")

# ==================== MAIN ====================
def main():
    global accounts_on_current_ip, current_session_id
    
    log("=" * 60)
    log("🚀 ACCOUNT CREATOR + ATTIVAZIONE AUTOMATICA")
    log("=" * 60)
    log(f"⚠️ Massimo {MAX_ACCOUNTS_PER_IP} account per IP (cambio automatico)")
    log("=" * 60)
    
    setup_output_dir()
    
    # Carica configurazione
    try:
        email_local, email_domain, default_password = load_register_config()
        log(f"📁 Configurazione caricata:")
        log(f"   email_local: {email_local}")
        log(f"   email_domain: {email_domain}")
    except FileNotFoundError as e:
        log(f"❌ {e}")
        return
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '1'))
    except:
        num_accounts = 1
    
    log(f"\n📊 Account da creare: {num_accounts}")
    log(f"🔑 Chiavi browserless disponibili: {len(VALID_KEYS)}")
    
    # Inizializza Mail.tm
    mail_activator = MailTMActivator()
    mail_activator.login()
    
    success_count = 0
    key_index = 0
    
    for i in range(num_accounts):
        log(f"\n{'='*60}")
        log(f"📝 CREAZIONE ACCOUNT {i+1}/{num_accounts}")
        log(f"{'='*60}")
        
        # Mostra stato IP
        if current_session_id is None:
            log(f"🌐 Primo IP - avvio nuova sessione")
        else:
            log(f"🌐 IP corrente: {current_session_id} ({accounts_on_current_ip}/{MAX_ACCOUNTS_PER_IP} account usati)")
        
        username = generate_username()
        email = build_email(username, email_local, email_domain)
        
        log(f"👤 Username: {username}")
        log(f"📧 Email: {email}")
        log(f"🔑 Password: {default_password}")
        
        # 1. Ottieni token (con cambio IP automatico se necessario)
        token = None
        for attempt in range(len(VALID_KEYS)):
            api_key = VALID_KEYS[(key_index + attempt) % len(VALID_KEYS)]
            log(f"🔑 Tentativo con chiave: {api_key[:20]}...")
            token = get_cf_token(api_key)
            if token:
                key_index = (key_index + attempt) % len(VALID_KEYS)
                log(f"✅ Token ottenuto!")
                break
            time.sleep(2)
        
        if not token:
            log(f"❌ Nessuna chiave funzionante")
            continue
        
        # 2. Registra
        cookies = register_with_token(token, username, email, default_password)
        
        if not cookies:
            log(f"❌ Registrazione fallita")
            continue
        
        log(f"✅ Registrazione riuscita! user_id: {cookies['user_id']}")
        
        # 3. Attiva via email
        mail_activator.set_target_email(email)
        activated = mail_activator.wait_for_activation(timeout_minuti=3)
        
        # 4. Salva
        save_account(username, email, default_password, cookies, activated)
        
        if activated:
            success_count += 1
            log(f"🎉 Account {i+1} completato (creato + attivato)!")
        else:
            log(f"⚠️ Account {i+1} creato ma NON attivato (timeout email)")
        
        # Se abbiamo raggiunto il limite di account per IP, forziamo cambio per il prossimo
        if accounts_on_current_ip >= MAX_ACCOUNTS_PER_IP and i < num_accounts - 1:
            log(f"⚠️ Raggiunto limite di {MAX_ACCOUNTS_PER_IP} account per IP")
            log(f"🔄 Prossimo account userà un nuovo IP")
        
        if i < num_accounts - 1:
            pause = random.randint(30, 60)
            log(f"⏸️ Pausa di {pause} secondi...")
            time.sleep(pause)
    
    log("\n" + "=" * 60)
    log(f"🏁 PROCESSO COMPLETATO!")
    log(f"✅ Account creati e attivati: {success_count}/{num_accounts}")
    log(f"📁 Output salvato in: {OUTPUT_DIR}/accounts.txt")
    log("=" * 60)

if __name__ == "__main__":
    main()
