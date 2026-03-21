#!/usr/bin/env python3
# app.py - Versione completa con gestione IP ottimizzata

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
# TUTTE LE 31 API KEY BROWSERLESS
VALID_KEYS = [
    # Vecchie chiavi
    "2UBQ8GwsajXwbXs10e72471480af4adaeb28a5a6a01ac89a7",
    "2UBQFmSYHD4NZGdb2f0eedc0e05b5de53a6746218bcdc139a",
    "2UBQLoR9eI8UsvL307891eb2aacfbb9a91978f37f010d2c29",
    "2UBTTPRPN6PFjLQdd5799398b26caf3a026c8ec3a9f9e5ad0",
    
    # Nuove chiavi
    "2UBnDTit4q9XEKDc5dd928eaaeeba1e19355f5790e6448609",
    "2UBnGaSy3OUY3GQ62740ff8c64d0d4e59234618332e5879f6",
    "2UBnL3CDkxjWE7Ef9fd7a3754e753f4a7df4a582343e67189",
    "2UBnPb0EAl96VbQ6adf224ec4c56e12bb19959eea41b57455",
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

# ==================== LIMITI IP ====================
MAX_ACCOUNTS_PER_IP = 3
accounts_on_current_ip = 0
current_session_id = None

# ==================== MAIL.TM CONFIG ====================
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
    global current_session_id, accounts_on_current_ip, stats
    current_session_id = random.randint(10000, 99999)
    accounts_on_current_ip = 0
    stats["ip_changes"] += 1
    log(f"🔄 NUOVO IP: Sessione {current_session_id} (cambio #{stats['ip_changes']})")
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
    log(f"   🌐 IP: {current_session_id} | Account {accounts_on_current_ip+1}/{MAX_ACCOUNTS_PER_IP} | Chiave: {api_key[:20]}...")
    
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
        response = requests.post(
            bql_url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 401:
            log(f"   ❌ Chiave 401 (non valida/esaurita)")
            return None
        elif response.status_code != 200:
            log(f"   ❌ HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            log(f"   ❌ Errore GraphQL: {data['errors'][0].get('message', 'Unknown')[:80]}")
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            solve_time = solve_info.get("time", "?")
            log(f"   ✅ Token ottenuto! ({len(token)} char, {solve_time}ms, totale {elapsed:.1f}s)")
            # Incrementa contatore account su questo IP
            accounts_on_current_ip += 1
            return token
        else:
            log(f"   ❌ Token non risolto (found={solve_info.get('found')})")
            return None
            
    except requests.exceptions.Timeout:
        log(f"   ❌ Timeout richiesta")
        return None
    except Exception as e:
        log(f"   ❌ Errore: {e}")
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
        log(f"   ✅ Registrazione OK! user_id: {final_cookies['user_id']}")
        return final_cookies
    else:
        log(f"   ❌ Registrazione fallita - URL: {response.url}")
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
            log("✅ Login Mail.tm OK")
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
        log(f"🔄 Attivazione...")
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
    
    def wait_for_activation(self, timeout_minuti=4):
        log(f"📧 Attesa email per {self.target_email}...")
        start = time.time()
        
        while time.time() - start < timeout_minuti * 60:
            try:
                message = self.get_activation_email()
                if message:
                    msg_id = message["id"]
                    
                    if msg_id == self.last_processed_id:
                        time.sleep(5)
                        continue
                    
                    log(f"📧 Email: {message['subject']}")
                    
                    res = self.session.get(f"{MAIL_BASE_URL}/messages/{msg_id}")
                    if res.status_code != 200:
                        time.sleep(5)
                        continue
                        
                    msg_data = res.json()
                    
                    body = msg_data.get("text") or msg_data.get("html", "")
                    link = self.extract_activation_link(body)
                    
                    if link:
                        log(f"🔗 Link attivazione trovato")
                        self.last_processed_id = msg_id
                        
                        success = self.activate_account(link)
                        return success
                    else:
                        log("⚠️ Link non trovato")
                        
                time.sleep(5)
                
            except Exception as e:
                log(f"⚠️ Polling error: {e}")
                time.sleep(5)
        
        log("❌ Timeout attivazione")
        return False

# ==================== SALVATAGGIO ====================
def save_account(username, email, password, cookies, activated=False):
    """Salva account in formato leggibile"""
    global stats
    
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
    
    # Salva in TXT nel formato richiesto
    status = "✅ ATTIVATO" if activated else "⏳ IN ATTESA"
    with open(f"{OUTPUT_DIR}/accounts.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}    Password {password}    {status}    IP:{current_session_id}\n")
    
    log(f"💾 Account salvato: {email}")
    
    if activated:
        stats["successful_activations"] += 1

# ==================== MAIN ====================
def main():
    global accounts_on_current_ip, current_session_id, stats
    
    log("=" * 70)
    log("🚀 EASYHITS4U ACCOUNT CREATOR v2.0")
    log("=" * 70)
    log(f"🔑 API key disponibili: {len(VALID_KEYS)}")
    log(f"⚠️ Massimo {MAX_ACCOUNTS_PER_IP} account per IP")
    log("=" * 70)
    
    setup_output_dir()
    
    # Carica configurazione
    try:
        email_local, email_domain, default_password = load_register_config()
        log(f"📁 Config: {email_local}@{email_domain} | Pwd: {default_password}")
    except FileNotFoundError as e:
        log(f"❌ {e}")
        log("   Crea register_config.json:")
        log('   {"email_local": "sandrominori50", "email_domain": "gmail.com", "password": "DDnmVV45!!"}')
        return
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '1'))
    except:
        num_accounts = 1
    
    log(f"\n📊 Account da creare: {num_accounts}")
    
    # Inizializza Mail.tm
    mail_activator = MailTMActivator()
    if not mail_activator.login():
        log("❌ Impossibile accedere a Mail.tm")
        return
    
    success_count = 0
    key_index = 0
    
    for i in range(num_accounts):
        log(f"\n{'='*70}")
        log(f"📝 ACCOUNT {i+1}/{num_accounts}")
        log(f"{'='*70}")
        
        # Mostra stato IP
        if current_session_id is None:
            log(f"🌐 Nuovo IP in arrivo...")
        else:
            log(f"🌐 IP corrente: {current_session_id} ({accounts_on_current_ip}/{MAX_ACCOUNTS_PER_IP} usati)")
        
        username = generate_username()
        email = build_email(username, email_local, email_domain)
        
        log(f"👤 {username}")
        log(f"📧 {email}")
        
        stats["total_attempts"] += 1
        
        # 1. Ottieni token (prova tutte le chiavi)
        token = None
        for attempt in range(len(VALID_KEYS)):
            api_key = VALID_KEYS[(key_index + attempt) % len(VALID_KEYS)]
            token = get_cf_token(api_key)
            if token:
                key_index = (key_index + attempt) % len(VALID_KEYS)
                stats["keys_used"][api_key[:20]] = stats["keys_used"].get(api_key[:20], 0) + 1
                break
            time.sleep(1)
        
        if not token:
            log(f"❌ Nessuna chiave funzionante dopo {len(VALID_KEYS)} tentativi")
            continue
        
        # 2. Registra
        cookies = register_with_token(token, username, email, default_password)
        
        if not cookies:
            log(f"❌ Registrazione fallita")
            continue
        
        stats["successful_registrations"] += 1
        
        # 3. Attiva via email
        mail_activator.set_target_email(email)
        activated = mail_activator.wait_for_activation(timeout_minuti=4)
        
        # 4. Salva
        save_account(username, email, default_password, cookies, activated)
        
        if activated:
            success_count += 1
            log(f"🎉 Account {i+1} COMPLETATO!")
        else:
            log(f"⚠️ Account {i+1} creato ma NON attivato")
        
        # Gestione cambio IP per prossimo account
        if accounts_on_current_ip >= MAX_ACCOUNTS_PER_IP:
            log(f"⚠️ Raggiunto limite {MAX_ACCOUNTS_PER_IP} account per IP")
            log(f"🔄 Prossimo account userà NUOVO IP")
            # Forza reset per il prossimo ciclo
            current_session_id = None
            accounts_on_current_ip = MAX_ACCOUNTS_PER_IP
        
        if i < num_accounts - 1:
            pause = random.randint(30, 60)
            log(f"⏸️ Pausa {pause}s...")
            time.sleep(pause)
    
    # Statistiche finali
    log("\n" + "=" * 70)
    log("📊 STATISTICHE FINALI")
    log("=" * 70)
    log(f"✅ Account completati: {success_count}/{num_accounts}")
    log(f"📈 Registrazioni: {stats['successful_registrations']}")
    log(f"📧 Attivazioni: {stats['successful_activations']}")
    log(f"🔄 Cambi IP: {stats['ip_changes']}")
    log(f"🔑 Chiavi utilizzate: {len(stats['keys_used'])}")
    log(f"📁 Output: {OUTPUT_DIR}/accounts.txt")
    log("=" * 70)

if __name__ == "__main__":
    main()
