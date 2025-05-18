import time
import threading
import sqlite3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def initialize_db():
    conn = sqlite3.connect("config.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            user_id TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def delete_user_id_from_db(user_id):
    try:
        conn = sqlite3.connect("config.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM urls WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        print(f"[INFO] user_id '{user_id}' deleted.")
    except Exception as e:
        print("Error delete user_id from DB:", e)

def add_user_id_to_db(user_id):
    try:
        conn = sqlite3.connect("config.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO urls (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        print(f"[INFO] Added user: {user_id}")
    except Exception as e:
        print("Error add user", e)

def get_urls_from_db():
    try:
        conn = sqlite3.connect("config.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM urls")
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        base_url = "https://odin.fun/user/{}?tab=activity"
        urls = [base_url.format(uid) for uid in user_ids]
        return urls
    except Exception as e:
        print("Error DB", e)
        return []

def check_and_filter(driver):
    try:
        wait = WebDriverWait(driver, 10)
        user_span = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'flex items-center gap-2')]//span")))
        username = user_span.text.strip()

        tbody = wait.until(EC.presence_of_element_located((By.XPATH, "//tbody[contains(@class, 'border-0')]")))
        soup = BeautifulSoup(tbody.get_attribute("outerHTML"), "html.parser")
        rows = soup.find_all("tr", limit=10)

        time_format = "%m/%d/%y %I:%M %p"
        now = datetime.now()

        valid_rows = []

        for row in rows:
            date_span = row.find("span", class_="text-odin-primary")
            if date_span:
                date_text = date_span.text.strip()
                row_time = datetime.strptime(date_text, time_format)

                if now - row_time <= timedelta(minutes=5):
                    token_name = "UNKNOWN"
                    action = "UNKNOWN"
                    quantity = "UNKNOWN"

                    token_span = row.find("span", class_="font-bold uppercase")
                    if token_span:
                        token_name = token_span.text.strip()

                    action_spans = row.find_all("span", class_="text-odin-primary")
                    if len(action_spans) > 1:
                        action = action_spans[1].text.strip()

                    price_span = row.find("span", string=lambda text: text and "$" in text)
                    if price_span:
                        quantity = price_span.text.strip()

                    formatted_output = f"{username} | {token_name} {action} {quantity}"
                    valid_rows.append((username, token_name, action, quantity))

        with open("filtered_output.txt", "a", encoding="utf-8") as file:
            for row in valid_rows:
                line = " | ".join(row)
                file.write(line + "\n")

    except Exception as e:
        print("Error", e)

def scraping_loop(stop_event):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        while not stop_event.is_set():
            urls = get_urls_from_db()
            for url in urls:
                driver.get(url)
                check_and_filter(driver)
            stop_event.wait(5 * 60)
    finally:
        driver.quit()

def menu():
    stop_event = threading.Event()
    scraper_thread = threading.Thread(target=scraping_loop, args=(stop_event,))
    scraper_thread.start()

    while True:
        print("\n==== MENU ====")
        print("1. ADD User user_id")
        print("2. Show user_id")
        print("3. Delete user_id")
        print("4. Stop & exit")
        choice = input("Input: ")

        if choice == "1":
            new_id = input("Write user_id: ").strip()
            if new_id:
                add_user_id_to_db(new_id)
        elif choice == "2":
            ids = get_urls_from_db()
            print("ID:")
            for url in ids:
                print(" -", url)
        elif choice == "3":
            delete_id = input("Write user_id: ").strip()
            if delete_id:
                delete_user_id_from_db(delete_id)
        elif choice == "4":
            stop_event.set()
            scraper_thread.join()
            print("Exit.")
            break
        else:
            print("Incorrect choice. Try again.")

if __name__ == "__main__":
    initialize_db()
    menu()
