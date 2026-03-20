#!/usr/bin/env python3
import time
import json
import random
import os
from datetime import datetime
from pathlib import Path
from seleniumbase import Driver
from turnstile_solver import solve

PASSWORD = os.environ.get('ACCOUNT_PASSWORD', 'Test123!@#')
OUTPUT_DIR = "/tmp/easyhits4u"
TURNSTILE_SITEKEY = "0x4AAAAAACHvZWqiG5m87_NE"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def generate_username():
    syllables = ["ka","lo","mi","ta","ne","za","ga","ra","chi","lu","no","be","ce","re","di","sa"]
    return "u" + "".join(random.choice(syllables) for _ in range(random.randint(3, 5)))

def create_account(username, email):
    driver = Driver(uc=True, headless=True, headless2=True, no_sandbox=True)
    try:
        driver.get(REFERER_URL)
        time.sleep(3)
        driver.find_element("css selector", "a[href*='join_popup_show']").click()
        time.sleep(2)
        driver.find_element("css selector", "#reg_form #name").send_keys(username)
        driver.find_element("css selector", "#reg_form #email").send_keys(email)
        driver.find_element("css selector", "#reg_form #login").send_keys(username)
        driver.find_element("css selector", "#reg_form #pass").send_keys(PASSWORD)
        driver.find_element("css selector", "#reg_form #cpass").send_keys(PASSWORD)
        
        if solve(driver, sitekey=TURNSTILE_SITEKEY, detect_timeout=15, solve_timeout=60):
            driver.find_element("css selector", "#reg_form input[type='submit']").click()
            time.sleep(5)
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            if 'user_id' in cookies:
                return cookies
    except Exception as e:
        log(f"Errore: {e}")
    finally:
        driver.quit()
    return None

def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    num = int(os.environ.get('NUM_ACCOUNTS', '1'))
    success = 0
    for i in range(num):
        username = generate_username()
        email = f"{username}@spaces0.com"
        log(f"Account {i+1}: {username}")
        cookies = create_account(username, email)
        if cookies:
            with open(f"{OUTPUT_DIR}/accounts.txt", "a") as f:
                f.write(f"{email}|{PASSWORD}|user_id:{cookies.get('user_id')}\n")
            success += 1
        time.sleep(random.randint(30, 60) if i < num-1 else 0)
    log(f"Creati: {success}/{num}")

if __name__ == "__main__":
    main()