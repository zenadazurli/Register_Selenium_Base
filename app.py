#!/usr/bin/env python3
# test_keys.py - Test semplice per verificare quali API key funzionano

import requests
import time

# Lista delle tue API key
API_KEYS = [
    "2UBQ5qEPkTsCBv63a4077ae6c54e5490f1efd231f724e110f",
    "2UBQ8GwsajXwbXs10e72471480af4adaeb28a5a6a01ac89a7",
    "2UBQFmSYHD4NZGdb2f0eedc0e05b5de53a6746218bcdc139a",
    "2UBQLoR9eI8UsvL307891eb2aacfbb9a91978f37f010d2c29",
    "2UBTTPRPN6PFjLQdd5799398b26caf3a026c8ec3a9f9e5ad0",
    "2UBTat16QAKVDOR88c3b1b6836641bd5f55430f575800ff78",
    "2UBTd0hz28QIgGp5c5fc4269d6cd26a941af72d22052682f5",
    "2UBTgezJiek8pHQ8bdff6b377db20b264b5a00e421252020b",
    "2UBTlkxuGKViNTIf7f751da9537acc8292659e39156640549",
    "2UBTo5odjkMG8zP704e449a8497f97225bacb4f6fc0018828",
    "2UBTs0B8NbkRU6M6cf0d942ca171dce7a413959445d684e40",
    "2UBTwKbgQv9SbWMbf8366d552af7dafe34abe844cbfc87412",
    "2UBU1WD3f3wombMbb42f047cd3692ee33c2ce927666c10d48",
    "2UBU7sUnS14V8QR35bfd5f6829b178f3ebb7da183d65f99ac",
    "2UBUBfSWWQkyIaxd4cf2cda7dbabfd44b7ad2af36c0b8b23f",
    "2UBUEFVcmXpE0PS2209857947a16ce9e62fa74a1e86089aa4",
    "2UBUIq0WVWh8YL0a74c45444695fb99cad649afdf2612ce2b",
    "2UBULlXV93BjB5q0584830febf5d19d27aa08496c268c5235",
]

BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

def test_key(api_key):
    """Testa se una chiave funziona"""
    print(f"🔑 Test chiave: {api_key[:20]}...", end=" ", flush=True)
    
    bql_url = f"{BROWSERLESS_URL}?token={api_key}"
    
    # Query minima per testare la connessione
    query = """
    query {
      status {
        available
        queueLength
        total
      }
    }
    """
    
    try:
        response = requests.post(
            bql_url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Error: {data['errors'][0].get('message', 'Unknown')[:50]}")
                return False
            else:
                status = data.get("data", {}).get("status", {})
                print(f"✅ OK (available: {status.get('available', '?')})")
                return True
        elif response.status_code == 401:
            print("❌ 401 - Chiave non valida/scaduta")
            return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 TEST API KEY BROWSERLESS")
    print("=" * 60)
    print(f"📊 Chiavi da testare: {len(API_KEYS)}\n")
    
    working_keys = []
    failed_keys = []
    
    for i, key in enumerate(API_KEYS, 1):
        print(f"[{i}/{len(API_KEYS)}] ", end="")
        if test_key(key):
            working_keys.append(key)
        else:
            failed_keys.append(key)
        time.sleep(0.5)  # Pausa tra richieste
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI")
    print("=" * 60)
    print(f"✅ Chiavi funzionanti: {len(working_keys)}")
    for key in working_keys:
        print(f"   {key[:20]}...")
    
    print(f"\n❌ Chiavi non funzionanti: {len(failed_keys)}")
    
    if working_keys:
        print("\n💡 Puoi usare queste chiavi:")
        print(",".join(working_keys))
    else:
        print("\n⚠️ Nessuna chiave funzionante. Devi ottenere nuove chiavi.")

if __name__ == "__main__":
    main()
