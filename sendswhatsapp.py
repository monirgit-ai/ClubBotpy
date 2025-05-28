import os
import time
import json
import random
import argparse
import sqlite3
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_PROFILE_PATH = os.path.join(BASE_DIR, "profile1")
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")
TEMP_DATA_PATH = os.path.join(BASE_DIR, "campaign_data.json")
DB_PATH = os.path.join(BASE_DIR, "db", "clubbot.db")

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")

def log_campaign(contact_number, message, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT rowid FROM contacts WHERE whatsapp = ?", (contact_number,))
        result = cursor.fetchone()
        contact_id = result[0] if result else None

        cursor.execute("""
            INSERT INTO campaign_reports (contact_id, message, status, sent_date)
            VALUES (?, ?, ?, datetime('now'))
        """, (contact_id, message, status))
        conn.commit()
        conn.close()
        print(f"📋 Report logged for {contact_number} [{status}]")
    except Exception as e:
        print(f"⚠️ Failed to log report for {contact_number}: {e}")

def open_whatsapp_only():
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get("https://web.whatsapp.com")
    print("✅ WhatsApp Web opened. Scan QR if needed.")
    input("⏳ Press Enter here to close the browser when you're done...\n")
    driver.quit()

def send_campaign_messages():
    with open(TEMP_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    numbers = data["numbers"]
    names = data.get("names", ["Friend"] * len(numbers))
    messages = data["messages"]
    mode = data["mode"]
    min_delay = data.get("min_delay", 5)
    max_delay = data.get("max_delay", 15)

    personalized_messages = []
    for idx, number in enumerate(numbers):
        name = names[idx]
        message_template = messages[0] if mode == "Same" else messages[idx % len(messages)]
        message = message_template.replace("{Name}", name)
        personalized_messages.append(message)
        print(f"➡️ Prepared for {number}: {message[:60]}...")

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get("https://web.whatsapp.com")
    print("✅ WhatsApp Web opened. Waiting to load...")
    time.sleep(10)

    for idx, number in enumerate(numbers):
        try:
            message = personalized_messages[idx]
            driver.get(f"https://web.whatsapp.com/send?phone={number}")
            input_xpath = "//div[@contenteditable='true' and @role='textbox' and contains(@aria-label, 'Type a message')]"

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, input_xpath))
            )
            msg_box = driver.find_element(By.XPATH, input_xpath)
            msg_box.click()
            time.sleep(1)

            # Clear existing content first to avoid duplication
            msg_box.send_keys(Keys.CONTROL + "a")
            msg_box.send_keys(Keys.DELETE)
            time.sleep(0.5)

            # Paste full message via clipboard
            pyperclip.copy(message)
            msg_box.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            msg_box.send_keys(Keys.ENTER)

            print(f"✅ Sent to {number}")
            log_campaign(number, message, "Sent")

            delay = random.randint(min_delay, max_delay)
            print(f"⏳ Waiting for {delay} seconds...")
            time.sleep(delay)

        except Exception as e:
            screenshot_path = os.path.join(BASE_DIR, f"error_{number}.png")
            driver.save_screenshot(screenshot_path)
            print(f"❌ Failed to send to {number}: {e} (screenshot saved to {screenshot_path})")
            log_campaign(number, personalized_messages[idx], "Failed")


        except Exception as e:
            screenshot_path = os.path.join(BASE_DIR, f"error_{number}.png")
            driver.save_screenshot(screenshot_path)
            print(f"❌ Failed to send to {number}: {e} (screenshot saved to {screenshot_path})")
            log_campaign(number, personalized_messages[idx], "Failed")

    driver.quit()
    print("🎉 Campaign completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    if args.open:
        open_whatsapp_only()
    elif args.send:
        send_campaign_messages()
