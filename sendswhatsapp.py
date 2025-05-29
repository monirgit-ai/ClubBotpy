import os
import time
import json
import random
import argparse
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_PROFILE_PATH = os.path.join(BASE_DIR, "profile1")
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")
TEMP_DATA_PATH = os.path.join(BASE_DIR, "campaign_data.json")
DB_PATH = os.path.join(BASE_DIR, "db", "clubbot.db")

options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")

# === DB Logging ===
def log_delivery(number, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO delivery_report (whatsapp, status, logged_at)
            VALUES (?, ?, datetime('now'))
        """, (number, status))
        conn.commit()
        conn.close()
        print(f"📋 Report logged for {number} [{status}]")
    except Exception as e:
        print(f"⚠️ Failed to log report for {number}: {str(e)}")

# === Open WhatsApp Only ===
def open_whatsapp_only():
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get("https://web.whatsapp.com")
    print("✅ WhatsApp Web opened. Scan QR if needed.")
    input("⏳ Press Enter here to close the browser when you're done...\n")
    driver.quit()

# === Send Messages ===
def send_campaign_messages():
    with open(TEMP_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    numbers = data["numbers"]
    messages = data["messages"]
    min_delay = int(data.get("min_delay", 1))
    max_delay = int(data.get("max_delay", 3))

    if len(numbers) != len(messages):
        print("❌ Mismatch: numbers and messages length differ")
        return

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get("https://web.whatsapp.com")
    print("✅ WhatsApp Web opened. Waiting to load...")
    time.sleep(10)

    for idx, number in enumerate(numbers):
        try:
            message = messages[idx]

            driver.get(f"https://web.whatsapp.com/send?phone={number}&text=")
            input_xpath = "//div[@contenteditable='true' and @role='textbox' and contains(@aria-label, 'Type a message')]"
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, input_xpath)))
            msg_box = driver.find_element(By.XPATH, input_xpath)
            msg_box.click()
            time.sleep(1)

            # Send line by line with SHIFT+ENTER for formatting
            lines = message.strip().split("\n")
            for i, line in enumerate(lines):
                msg_box.send_keys(line)
                if i < len(lines) - 1:
                    msg_box.send_keys(Keys.SHIFT + Keys.ENTER)
            msg_box.send_keys(Keys.ENTER)

            print(f"✅ Sent to {number}")
            log_delivery(number, "Sent")

            delay = random.randint(min_delay, max_delay)
            print(f"⏳ Waiting for {delay} seconds...")
            time.sleep(delay)

        except Exception as e:
            screenshot_path = os.path.join(BASE_DIR, f"error_{number}.png")
            driver.save_screenshot(screenshot_path)
            print(f"❌ Failed to send to {number}: {e} (screenshot saved)")
            log_delivery(number, "Failed")

    driver.quit()
    print("🎉 Campaign completed.")

# === MAIN ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true", help="Open WhatsApp only")
    parser.add_argument("--send", action="store_true", help="Send campaign messages")
    args = parser.parse_args()

    if args.open:
        open_whatsapp_only()
    elif args.send:
        send_campaign_messages()
