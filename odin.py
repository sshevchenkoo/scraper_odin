import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Настройки без интерфейса
options = Options()
options.add_argument("--headless")  # Убрать, если хотите видеть браузер
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Функция для фильтрации данных
def check_and_filter(driver):
    try:
        # Ждем загрузку таблицы
        wait = WebDriverWait(driver, 10)
        tbody = wait.until(EC.presence_of_element_located((By.XPATH, "//tbody[contains(@class, 'border-0')]")))

        # Получаем HTML содержимое и парсим с помощью BeautifulSoup
        soup = BeautifulSoup(tbody.get_attribute("outerHTML"), "html.parser")

        # Находим первые 10 блоков <tr>
        rows = soup.find_all("tr", limit=10)

        # Формат даты в HTML
        time_format = "%m/%d/%y %I:%M %p"

        # Текущее время
        now = datetime.now()

        # Фильтрация строк по дате
        valid_rows = []
        for row in rows:
            # Ищем <span> с классом text-odin-primary
            date_span = row.find("span", class_="text-odin-primary")
            if date_span:
                # Преобразуем текст даты в datetime
                date_text = date_span.text.strip()
                row_time = datetime.strptime(date_text, time_format)

                # Проверяем, входит ли разница во временной интервал 5 минут
                if now - row_time <= timedelta(minutes=60):
                    soup = BeautifulSoup(str(row), "html.parser")
                    # Извлекаем название токена
                    token_span = soup.find("span", class_="font-bold uppercase")
                    token_name = token_span.text.strip() if token_span else "UNKNOWN"
                    # Извлекаем действие (BUY/SELL)
                    action_span = soup.find_all("span", class_="text-odin-primary")
                    action = action_span[1].text.strip() if len(action_span) > 1 else "UNKNOWN"
                    # Извлекаем количество
                    quantity_span = soup.find_all("span", class_="")
                    quantity = quantity_span[0].text.strip() if quantity_span else "UNKNOWN"
                    # Выводим в читаемом формате
                    formatted_output = f"{token_name} {action} {quantity}"
                    print(formatted_output)
                    valid_rows.append(row)

        # Формируем HTML для отфильтрованных строк
        valid_rows_html = "".join([str(row) for row in valid_rows])

        # Сохраняем в файл
        with open("filtered_output.html", "w", encoding="utf-8") as file:
            file.write(valid_rows_html)

        print(f"Проверка завершена. Найдено строк: {len(valid_rows)}")

    except Exception as e:
        print("Ошибка при обработке данных:", e)

# Запуск браузера и постоянное обновление
try:
    # Запускаем браузер один раз
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Загружаем страницу один раз
    url = "https://odin.fun/user/zbbno-hxlzc-zqcxy-stoni-dnqrl-zbfdu-qo3bt-6xkww-mz6zl-bc6gy-lqe?tab=activity"
    driver.get(url)

    # Основной цикл проверки каждые 5 минут
    while True:
        check_and_filter(driver)
        print("Ожидание 5 минут...")
        time.sleep(5 * 60)  # Задержка в 5 минут

except KeyboardInterrupt:
    print("Программа остановлена пользователем.")

except Exception as e:
    print("Ошибка:", e)

finally:
    # Закрываем браузер
    driver.quit()
