import requests
from bs4 import BeautifulSoup
from telegram.ext import Application
import asyncio
import time 


TELEGRAM_BOT_TOKEN = 'xxxxx' #enter your bot token 

TELEGRAM_CHANNEL_ID = -xxxxxxx# Example: -1001234567890 enter urs 


CHECK_INTERVAL_SECONDS = 3600

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Connection': 'keep-alive'
}

# thi is the scraping part 
def scrape_amazon_product(url, headers):

    print(f"Attempting to scrape: {url}")

    response = requests.get(url, headers=headers, timeout=15)
    # Raise an HTTPError for bad responses (4xx or 5xx status codes).
    response.raise_for_status()
    
    
    soup = BeautifulSoup(response.text, 'lxml')

    # Find the product title.
    title_element = soup.select_one('#productTitle')
    title = title_element.get_text(strip=True) if title_element else "Product title not found"


    price_whole_span = soup.find('span', class_='a-price-whole')
    
    price_text = None
    if price_whole_span:

        price_text = price_whole_span.get_text(strip=True).replace(",", "")


    print(f"Title: {title}")
    print(f"Scraped Price : {price_text}")

    # Convert price text to a float 
    if price_text and price_text.replace('.', '', 1).isdigit(): 
        current_price = float(price_text)
        return title, current_price
    else:
        print(f"Could not parse price '{price_text}' as a number or price element not found.")
        return title, None # Return None for price if it can't be converted or not found


# for sending to  tg channel
async def send_to_telegram_channel(application, message):

    await application.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode='HTML')
    print(f"Message sent to Telegram channel.")

async def main():
 
    # Initialize the Telegram bot application.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    
    product_url = input("Please enter the Amazon product URL: ").strip()
    
    while not (product_url.startswith("http://") or product_url.startswith("https://")):
        print("Invalid URL. Please enter a full URL starting with 'http://' or 'https://'.")
        product_url = input("Please enter the Amazon product URL: ").strip()


    target_price_str = input("Please enter your target price  ").strip()
    while True:
        try:
            target_price = float(target_price_str)
            if target_price <= 0:
                raise ValueError("Target price must be a positive number.")
            break # Exit loop if input is valid
        except ValueError:
            print("Invalid target price. Please enter a valid number (e.g., 45000.00).")
            target_price_str = input("Please enter your target price: ").strip()

    print(f"\n--- Starting Price Tracker ---")
    print(f"Monitoring product: {product_url}")
    print(f"Your target price: INR {target_price:,.2f}")
    print(f"Checking every {CHECK_INTERVAL_SECONDS} seconds (~{CHECK_INTERVAL_SECONDS / 60:.0f} minutes or {CHECK_INTERVAL_SECONDS / 3600:.1f} hours)...\n")

    last_notified_price = None # To prevent repeated alerts for the same price below target

    # this loop to the moon
    while True:
        print(f"\nInitiating price check...")
        
        # Scrape the current product details.
        product_title, current_price = scrape_amazon_product(product_url, headers)

        if current_price is not None:
            # If price found and parsed successfully
            if current_price <= target_price:
                # Price is at or below target - send an alert!
                if last_notified_price is None or current_price < last_notified_price:
                    # Only send if it's the first time hitting the target, or if the price dropped further
                    message = (
                        
                        f"<b>Product:</b> {product_title}\n"
                        f"<b>Current Price:</b> INR {current_price:,.2f}\n"
                        f"<b>Your Target:</b> INR {target_price:,.2f}\n"
                        f"The price has dropped to or below your target!\n"
                        f"<a href='{product_url}'>click to open on Amazon</a>"
                    )
                    await send_to_telegram_channel(application, message)
                    print(f"Price is at or below target ({current_price}). Sent alert.")
                    last_notified_price = current_price
                else:
                    print(f"Price ({current_price}) is still at or below target, but not lower than last notified price. No new alert sent.")
            else:
                # Price is still above target.
                message = (
                    f"🔔 <b>Price Check Update</b> 🔔\n\n"
                    f"<b>Product:</b> {product_title}\n"
                    f"<b>Current Price:</b> INR {current_price:,.2f}\n"
                    f"<b>Your Target:</b> INR {target_price:,.2f}\n"
                    f"The price is currently above your target.\n"
                    f"Last checked: (Most Recent Check)" # Updated to a static string
                )
                print(f"Price ({current_price}) is still above target. No alert needed yet.")

                last_notified_price = None # Reset if price goes above target again

        print(f"Waiting for {CHECK_INTERVAL_SECONDS} seconds before next check...\n")
        # Pause for interval.
        time.sleep(CHECK_INTERVAL_SECONDS) 


if __name__ == '__main__':

    asyncio.run(main())
