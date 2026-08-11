import requests
from bs4 import BeautifulSoup
import os

# ============================
# CONFIGURAZIONE
# ============================

# PHARMASHOPI
PRODUCT_URL = "https://www.pharmashopi.com/minoxidil-bailleul-solution-pour-application-cutanee-homme-flacons-de-60ml-xml-704_24979_24894-140875.html#product-info-detailed-anchor"
TARGET_PRICE = 17.98

# AMAZON – pagina del prodotto
AMAZON_URL = "https://www.amazon.it/dp/B0G3YJ6DBZ"

# TELEGRAM
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# ============================
# FUNZIONE TELEGRAM
# ============================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data)
    print("Telegram response:", r.text)


# ============================
# PHARMASHOPI SCRAPER
# ============================

def get_pharmashopi_price():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "it-IT,it;q=0.9"
    }
    r = requests.get(PRODUCT_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    price_span = soup.select_one("span.price")
    if not price_span:
        return None

    price_text = price_span.get_text(strip=True)
    price_text = price_text.replace("€", "").replace(",", ".")
    return float(price_text)


# ============================
# AMAZON SCRAPER (USO FRASE)
# ============================

def get_amazon_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "it-IT,it;q=0.9"
    }

    r = requests.get(AMAZON_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # 1) SE compare la frase → NON disponibile
    unavailable_phrase = soup.find(string=lambda t: t and "Prezzo più alto di quello abituale" in t)
    if unavailable_phrase:
        return None

    # 2) SE la frase NON compare → prodotto disponibile → estrai il prezzo

    # Versione accessibile
    offscreen = soup.select_one(".a-price .a-offscreen")
    if offscreen:
        txt = offscreen.get_text(strip=True)
        txt = txt.replace("€", "").replace(",", ".")
        try:
            return float(txt)
        except:
            return None

    # Prezzo spezzato
    whole = soup.select_one(".a-price .a-price-whole")
    fraction = soup.select_one(".a-price .a-price-fraction")

    if whole and fraction:
        price_text = whole.get_text(strip=True) + "." + fraction.get_text(strip=True)
        price_text = price_text.replace("€", "")
        try:
            return float(price_text)
        except:
            return None

    return None


# ============================
# MAIN
# ============================

def main():

    # PHARMASHOPI
    price = get_pharmashopi_price()
    print(f"Pharmashopi prezzo attuale: {price}")

    if price is not None and price <= TARGET_PRICE:
        send_telegram(f"🔥 Prezzo Pharmashopi sceso a {price} €!\n{PRODUCT_URL}")
    else:
        print("Pharmashopi: nessuna notifica.")

    # AMAZON
    amazon_price = get_amazon_price()
    print(f"Amazon prezzo attuale: {amazon_price}")

    if amazon_price is not None:
        send_telegram(
            f"🟢 Il prodotto Amazon è DISPONIBILE!\n"
            f"Prezzo: {amazon_price} €\n"
            f"{AMAZON_URL}"
        )
    else:
        print("Amazon: ancora non disponibile.")


if __name__ == "__main__":
    main()
