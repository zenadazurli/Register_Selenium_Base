#!/usr/bin/env python3
# app.py - Versione completa con debug email e ottimizzazioni

import requests
import json
import time
import random
import re
import os
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURAZIONE ====================
# SOLO CHIAVI CHE HANNO FUNZIONATO (dai test)
VALID_KEYS = [
    # Chiavi che hanno funzionato nei test
    "2UBnPb0EAl96VbQ6adf224ec4c56e12bb19959eea41b57455",  # Ha funzionato
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

# ==================== LIMITI IP ====================
MAX_ACCOUNTS_PER_IP = 3
accounts_created = 0
current_ip_session = None

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

def get_new_ip_session():
    """Genera una nuova sessione per ottenere un IP diverso"""
    global current_ip_session, accounts_created, stats
    current_ip_session = f"{int(time.time())}_{random.randint(1000, 9999)}"
    accounts_created = 0
    stats["ip_changes"] += 1
    log(f"🔄 NUOVO IP: Sessione {current_ip_session} (cambio #{stats['ip_changes']})")
    return current_ip_session

def get_browserless_url(api_key):
    """Costruisce URL con sessione unica per IP diverso"""
    global current_ip_session, accounts_created
    
    if current_ip_session is None or accounts_created >= MAX_ACCOUNTS_PER_IP:
        get_new_ip_session()
    
    bql_url = f"{BROWSERLESS_URL}?token={api_key}&stealth=true&proxy=residential&proxyCountry=it&session={current_ip_session}"
    
    return bql_url

def get_cf_token(api_key):
    """Ottiene CF token con IP diverso ogni 3 account"""
    global accounts_created, stats
    
    bql_url = get_browserless_url(api_key)
    log(f"   🌐 Sessione: {current_ip_session} | Account {accounts_created+1}/{MAX_ACCOUNTS_PER_IP} | Chiave: {api_key[:20]}...")
    
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
            log(f"   ❌ Errore: {data['errors'][0].get('message', 'Unknown')[:80]}")
            return None
        
        solve_info = data.get("data", {}).get("solve", {})
        
        if solve_info.get("solved"):
            token = solve_info.get("token")
            solve_time = solve_info.get("time", "?")
            log(f"   ✅ Token ottenuto! ({len(token)} char, {solve_time}ms, {elapsed:.1f}s)")
            accounts_created += 1
            stats["keys_used"][api_key[:20]] = stats["keys_used"].get(api_key[:20], 0) + 1
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
        stats["successful_registrations"] += 1
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
            log("🔐 Login Mail.tm...")
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
    
    def get_all_messages(self):
        """Recupera tutti i messaggi dalla inbox"""
        try:
            res = self.session.get(f"{MAIL_BASE_URL}/messages")
            if res.status_code == 200:
                return res.json().get("hydra:member", [])
        except Exception as e:
            log(f"⚠️ Errore recupero messaggi: {e}")
        return []
        
    def get_activation_email(self):
        """Cerca email di attivazione"""
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
        except Exception as e:
            log(f"⚠️ Errore ricerca email: {e}")
        return None
    
    def extract_activation_link(self, text):
        """Estrae il link di attivazione dal corpo dell'email"""
        try:
            # Pattern per il link di attivazione
            patterns = [
                r'(https?://)?www\.easyhits4u\.com/\?emlac=[^\s\]"\']+',
                r'href=["\'](https?://www\.easyhits4u\.com/\?emlac=[^"\']+)["\']',
                r'(https?://www\.easyhits4u\.com/\?emlac=[^\s]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    link = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    if not link.startswith("http"):
                        link = "https://" + link
                    return link
        except Exception as e:
            log(f"⚠️ Errore estrazione link: {e}")
        return None
    
    def activate_account(self, link):
        """Apre il link di attivazione"""
        try:
            log(f"🔗 Apertura link attivazione...")
            r = requests.get(link, timeout=15, allow_redirects=True)
            final_url = r.url
            log(f"   URL finale: {final_url}")
            
            if "email_ok" in final_url or "mail_activated" in final_url or "account_activated" in final_url:
                log(f"✅ Attivazione completata!")
                return True
            else:
                log(f"⚠️ Attivazione: status {r.status_code}")
                return False
        except Exception as e:
            log(f"❌ Errore attivazione: {e}")
            return False
    
    def wait_for_activation(self, timeout_minuti=6):
        """Attende l'email di attivazione con debug dettagliato"""
        log(f"📧 Attesa email per {self.target_email}...")
        log(f"   Timeout: {timeout_minuti} minuti")
        
        # Mostra email già presenti
        try:
            messages = self.get_all_messages()
            log(f"📨 Email presenti nella inbox: {len(messages)}")
            for i, msg in enumerate(messages[:5]):
                to_addr = msg.get("to", [{}])[0].get("address", "N/A") if msg.get("to") else "N/A"
                log(f"   {i+1}. {msg.get('subject', 'N/A')[:50]} -> {to_addr}")
        except Exception as e:
            log(f"⚠️ Impossibile leggere inbox: {e}")
        
        start = time.time()
        check_count = 0
        
        while time.time() - start < timeout_minuti * 60:
            check_count += 1
            elapsed = int(time.time() - start)
            
            try:
                # Cerca email di attivazione
                message = self.get_activation_email()
                
                if message:
                    msg_id = message["id"]
                    
                    # Evita di processare la stessa email due volte
                    if msg_id == self.last_processed_id:
                        log(f"⏳ Già processata, attendo nuova... ({elapsed}s)")
                        time.sleep(10)
                        continue
                    
                    log(f"📧 EMAIL DI ATTIVAZIONE TROVATA! (dopo {elapsed}s)")
                    log(f"   Oggetto: {message['subject']}")
                    log(f"   Mittente: {message.get('from', {}).get('address', 'N/A')}")
                    
                    # Recupera il corpo del messaggio
                    res = self.session.get(f"{MAIL_BASE_URL}/messages/{msg_id}")
                    if res.status_code != 200:
                        log(f"⚠️ Impossibile leggere il messaggio: {res.status_code}")
                        time.sleep(5)
                        continue
                        
                    msg_data = res.json()
                    
                    # Cerca il link in text o html
                    body = ""
                    if msg_data.get("text"):
                        body += msg_data["text"]
                    if msg_data.get("html"):
                        body += msg_data["html"]
                    
                    link = self.extract_activation_link(body)
                    
                    if link:
                        log(f"🔗 Link attivazione: {link[:100]}...")
                        self.last_processed_id = msg_id
                        success = self.activate_account(link)
                        return success
                    else:
                        log("⚠️ Link non trovato nel corpo dell'email")
                        # Salva il corpo per debug
                        debug_file = f"{OUTPUT_DIR}/email_debug_{self.target_email}.html"
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(body)
                        log(f"💾 Email salvata in: {debug_file}")
                        
                else:
                    if check_count % 6 == 0:  # Log ogni minuto circa
                        log(f"⏳ Nessuna email di attivazione... ({elapsed}s / {timeout_minuti*60}s)")
                        
            except Exception as e:
                log(f"⚠️ Errore durante polling: {e}")
            
            time.sleep(10)  # Polling ogni 10 secondi
        
        log(f"❌ Timeout attivazione dopo {timeout_minuti} minuti")
        return False

# ==================== SALVATAGGIO ====================
def save_account(username, email, password, cookies, activated=False):
    """Salva account in formato leggibile"""
    status = "✅ ATTIVATO" if activated else "⏳ IN ATTESA"
    session_info = current_ip_session if current_ip_session else "N/A"
    
    with open(f"{OUTPUT_DIR}/accounts.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}    Password {password}    [{status}]    Sessione:{session_info}    user_id:{cookies.get('user_id', 'N/A')}\n")
    
    log(f"💾 Account salvato: {email} [{status}] IP:{session_info}")
    
    if activated:
        stats["successful_activations"] += 1

# ==================== MAIN ====================
def main():
    global accounts_created, current_ip_session, stats
    
    log("=" * 70)
    log("🚀 EASYHITS4U ACCOUNT CREATOR v4.0")
    log("=" * 70)
    log(f"🔑 API key disponibili: {len(VALID_KEYS)}")
    log(f"⚠️ Massimo {MAX_ACCOUNTS_PER_IP} account per IP (cambio automatico)")
    log(f"📧 Mail.tm: {MAIL_EMAIL}")
    log("=" * 70)
    
    setup_output_dir()
    
    # Carica configurazione
    try:
        email_local, email_domain, default_password = load_register_config()
        log(f"📁 Config: {email_local}@{email_domain}")
    except FileNotFoundError as e:
        log(f"❌ {e}")
        log("   Crea register_config.json:")
        log('   {"email_local": "sandrominori50", "email_domain": "gmail.com", "password": "DDnmVV45!!"}')
        return
    
    try:
        num_accounts = int(os.environ.get('NUM_ACCOUNTS', '3'))
    except:
        num_accounts = 3
    
    log(f"📊 Account da creare: {num_accounts}")
    
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
        if current_ip_session is None:
            log(f"🌐 Primo IP - avvio nuova sessione")
        else:
            log(f"🌐 IP corrente: {current_ip_session} ({accounts_created}/{MAX_ACCOUNTS_PER_IP} usati)")
        
        username = generate_username()
        email = build_email(username, email_local, email_domain)
        
        log(f"👤 Username: {username}")
        log(f"📧 Email: {email}")
        log(f"🔑 Password: {default_password}")
        
        stats["total_attempts"] += 1
        
        # 1. Ottieni token (prova tutte le chiavi)
        token = None
        for attempt in range(len(VALID_KEYS)):
            api_key = VALID_KEYS[(key_index + attempt) % len(VALID_KEYS)]
            token = get_cf_token(api_key)
            if token:
                key_index = (key_index + attempt) % len(VALID_KEYS)
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
        
        # 3. Attiva via email
        mail_activator.set_target_email(email)
        activated = mail_activator.wait_for_activation(timeout_minuti=6)
        
        # 4. Salva
        save_account(username, email, default_password, cookies, activated)
        
        if activated:
            success_count += 1
            log(f"🎉 Account {i+1} COMPLETATO (creato + attivato)!")
        else:
            log(f"⚠️ Account {i+1} creato ma NON attivato")
        
        # 5. Pausa tra account
        if i < num_accounts - 1:
            pause = random.randint(30, 60)
            log(f"⏸️ Pausa di {pause} secondi...")
            time.sleep(pause)
    
    # Statistiche finali
    log("\n" + "=" * 70)
    log("📊 STATISTICHE FINALI")
    log("=" * 70)
    log(f"✅ Account completati (attivati): {success_count}/{num_accounts}")
    log(f"📈 Registrazioni riuscite: {stats['successful_registrations']}")
    log(f"📧 Attivazioni riuscite: {stats['successful_activations']}")
    log(f"🔄 Cambi IP effettuati: {stats['ip_changes']}")
    log(f"🔑 Chiavi utilizzate: {len(stats['keys_used'])}")
    log(f"📁 Output: {OUTPUT_DIR}/accounts.txt")
    log("=" * 70)
    
    # Mostra riepilogo account
    if Path(f"{OUTPUT_DIR}/accounts.txt").exists():
        log("\n📋 RIEPILOGO ACCOUNT:")
        with open(f"{OUTPUT_DIR}/accounts.txt", "r") as f:
            for line in f:
                log(f"   {line.strip()}")

if __name__ == "__main__":
    main()
