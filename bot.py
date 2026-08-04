import requests
from bs4 import BeautifulSoup
import os

PRODUCT_URL = "https://www.pharmashopi.com/minoxidil-bailleul-solution-pour-application-cutanee-homme-flacons-de-60ml-xml-704_24979_24894-140875.html#product-info-detailed-anchor"
TARGET_PRICE = 100.00

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_price():
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
    try:
        return float(price_text)
    except:
        return None

def main():
    price = get_price()
    print(f"Prezzo attuale: {price}")

    if price is not None and price <= TARGET_PRICE:
        send_telegram(f"🔥 Prezzo sceso a {price} €!\n{PRODUCT_URL}")
    else:
        print("Nessuna notifica.")

if __name__ == "__main__":
    main()
