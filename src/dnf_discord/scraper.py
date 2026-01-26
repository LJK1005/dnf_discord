import time
from typing import Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from .parser import parse_korean_number


STAT_NAME_MAP = {
    "랭킹": "ranking",
    "버프점수": "buff_score",
    "2인": "party2",
    "4인": "party4",
}

ENTRY_XPATH = "/html/body/div/div/div/div/section/div[1]/div[4]/div"
UNIQUE_NAME_SELECTOR = "div.seh_name > span > span"
STAT_A_NAME_SELECTOR = "div.seh_stat > ul.stat_a > li > div > span.tl.tfive"
STAT_A_VALUE_SELECTOR = "div.seh_stat > ul.stat_a > li > div > span.val"
STAT_B_NAME_2_SELECTOR = "div.seh_stat > ul.stat_b > li:nth-child(1) > div > span.tl"
STAT_B_NAME_4_SELECTOR = "div.seh_stat > ul.stat_b > li:nth-child(3) > div > span.tl"
STAT_B_VALUE_2_SELECTOR = "div.seh_stat > ul.stat_b > li:nth-child(1) > div > span.val"
STAT_B_VALUE_4_SELECTOR = "div.seh_stat > ul.stat_b > li:nth-child(3) > div > span.val"


def build_driver(chromedriver_path: str) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")

    service = Service(chromedriver_path)
    return webdriver.Chrome(service=service, options=options)


def scrape_character_stats(
    driver: webdriver.Chrome,
    account_name: str,
    nickname: str,
    wait_seconds: int = 5,
) -> Dict[str, int]:
    url = f"https://dundam.xyz/search?server=all&name={nickname}"
    driver.get(url)
    time.sleep(wait_seconds)

    entries = driver.find_elements(by=By.XPATH, value=ENTRY_XPATH)
    for entry in entries:
        try:
            unique_name = entry.find_element(
                by=By.CSS_SELECTOR, value=UNIQUE_NAME_SELECTOR
            ).text
        except Exception:
            continue

        if unique_name != account_name:
            continue

        return _parse_entry(entry)

    return {}


def _parse_entry(entry) -> Dict[str, int]:
    try:
        stat_name = entry.find_element(by=By.CSS_SELECTOR, value=STAT_A_NAME_SELECTOR).text
        stat_value = entry.find_element(
            by=By.CSS_SELECTOR, value=STAT_A_VALUE_SELECTOR
        ).text
        stat_value = stat_value.replace(" ", "")
        parsed_value = parse_korean_number(stat_value)
        key = STAT_NAME_MAP.get(stat_name.strip())
        if key and parsed_value:
            return {key: parsed_value}
        return {}
    except Exception:
        return _parse_entry_stat_b(entry)


def _parse_entry_stat_b(entry) -> Dict[str, int]:
    stats: Dict[str, int] = {}

    try:
        stat_name_2 = entry.find_element(by=By.CSS_SELECTOR, value=STAT_B_NAME_2_SELECTOR).text
        stat_value_2 = entry.find_element(
            by=By.CSS_SELECTOR, value=STAT_B_VALUE_2_SELECTOR
        ).text
        stat_value_2 = int(stat_value_2.replace(" ", "").replace(",", ""))
        key_2 = STAT_NAME_MAP.get(stat_name_2.strip())
        if key_2 and stat_value_2:
            stats[key_2] = stat_value_2
    except Exception:
        pass

    try:
        stat_name_4 = entry.find_element(by=By.CSS_SELECTOR, value=STAT_B_NAME_4_SELECTOR).text
        if stat_name_4:
            stat_value_4 = entry.find_element(
                by=By.CSS_SELECTOR, value=STAT_B_VALUE_4_SELECTOR
            ).text
            stat_value_4 = int(stat_value_4.replace(" ", "").replace(",", ""))
            key_4 = STAT_NAME_MAP.get(stat_name_4.strip())
            if key_4 and stat_value_4:
                stats[key_4] = stat_value_4
    except Exception:
        pass

    return stats
