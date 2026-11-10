import requests
from bs4 import BeautifulSoup
import os
import re
import json

# ============================
# CONFIGURAZIONE
# ============================

# PHARMASHOPI
PRODUCT_URL = "https://www.pharmashopi.com/minoxidil-bailleul-solution-pour-application-cutanee-homme-flacons-de-60ml-xml-704_24979_24894-140875.html#product-info-detailed-anchor"
TARGET_PRICE = 17.98

# TELEGRAM
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ============================
# FUNZIONE TELEGRAM
# ============================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data, timeout=15)
    print("Telegram response:", r.text)

# ============================
# UTILS PREZZO
# ============================

def parse_price_text(text):
    """'18,90 €' / '18.90' / '18,90' -> 18.90, oppure None"""
    if not text:
        return None
    # toglie spazi, nbsp, €
    text = str(text).replace("\xa0", "").replace("€", "").strip()
    # prende solo il primo numero tipo 18,90 o 18.90
    m = re.search(r"(\d+[.,]\d{2}|\d+)", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None

# ============================
# PHARMASHOPI SCRAPER
# ============================

def get_pharmashopi_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,it-IT;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        r = requests.get(PRODUCT_URL, headers=headers, timeout=20)
        print(f"Status Pharmashopi: {r.status_code} len: {len(r.text)}")
        if r.status_code != 200:
            return None
    except Exception as e:
        print(f"Errore richiesta Pharmashopi: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 1) JSON-LD - il metodo più affidabile su Prestashop
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            # può essere dict o lista
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                offers = item.get("offers")
                if isinstance(offers, dict) and "price" in offers:
                    price = parse_price_text(offers["price"])
                    if price:
                        return price
                if "price" in item:
                    price = parse_price_text(item["price"])
                    if price:
                        return price
        except Exception:
            continue

    # 2) Meta property product:price:amount
    meta = soup.find("meta", property="product:price:amount")
    if meta and meta.get("content"):
        price = parse_price_text(meta["content"])
        if price:
            return price

    # 3) itemprop=price (spesso ha content="18.90" anche se il testo è vuoto)
    tag = soup.select_one("[itemprop='price']")
    if tag:
        price = parse_price_text(tag.get("content") or tag.get_text(strip=True))
        if price:
            return price

    # 4) Vecchio selettore, ma con controllo anti-vuoto
    for sel in ["span.price", ".current-price", ".product-price", "#our_price_display"]:
        price_span = soup.select_one(sel)
        if price_span:
            price = parse_price_text(price_span.get_text(strip=True))
            if price:
                return price

    # 5) Fallback regex sull'HTML grezzo - cerca "18,90 €"
    m = re.search(r"(\d{1,3}[.,]\d{2})\s*€", r.text)
    if m:
        return parse_price_text(m.group(1))

    print("Prezzo non trovato - debug: primi 500 caratteri HTML:")
    print(r.text[:500])
    return None

# ============================
# MAIN
# ============================

def main():
    # PHARMASHOPI
    price = get_pharmashopi_price()
    print(f"Pharmashopi prezzo attuale: {price}")

    if price is None:
        print("Pharmashopi: prezzo non trovato, salto notifica.")
        return

    if price <= TARGET_PRICE:
        send_telegram(f"🔥 Prezzo Pharmashopi sceso a {price} €!\n{PRODUCT_URL}")
    else:
        print("Pharmashopi: nessuna notifica.")

if __name__ == "__main__":
    main()
