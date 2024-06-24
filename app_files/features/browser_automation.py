import logging
import os
import random
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import chromedriver_binary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
from datetime import datetime
from ics import Calendar, Event
from datetime import datetime
from dateutil.parser import parse

# base_url = "https://www.airbnb.at/rooms/867584026454825212?adults=1&category_tag=Tag%3A8535&children=0&enable_m3_private_room=true&infants=0&pets=0&photo_id=1679922251&search_mode=flex_destinations_search&check_in=2024-06-09&check_out=2024-06-14&source_impression_id=p3_1717003753_xYthhn%2FuYunQcuGi&previous_page_section_name=1000"
# TOTAL_NUMBER_OF_MONTHS_TO_LOOKUP = 6


class RootScraper():
    def __init__(
            self,
            headless: Optional[bool] = True,
            user_agent: Optional[str] = None,
            proxy: Optional[str] = None,
            element_load_timeout: Optional[int] = 20,
            page_load_timeout: Optional[int] = None,
    ):
        self.headless = headless
        self.user_agent = user_agent
        self.proxy = proxy
        self.element_load_timeout = element_load_timeout
        self.page_load_timeout = page_load_timeout
        self.driver = None

    def open_chromedriver(self):
        if self.driver:
            print(f"Driver already open, close is first.")
            return
        chrome_path = chromedriver_binary.chromedriver_filename
        os.chmod(chrome_path, 0o755)
        service = Service(executable_path=chrome_path)
        options = webdriver.ChromeOptions()
        all_args = [
            '--disable-gpu',
            '--disable-blink-features=AutomationControlled',
            '--log-level=0',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content',
            '--no-sandbox',
            "--window-size=1280x1696",
            "--single-process",
            "--disable-dev-shm-usage",
            "--disable-dev-tools",
            "--no-zygote",
        ]
        if self.user_agent:
            all_args.append(f'user-agent={self.user_agent}')
        else:
            all_args.append(f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        if self.headless:
            all_args.append("--headless=new")
        if self.proxy:
            all_args.append('--proxy-server={proxy}')
        for arg in all_args:
            options.add_argument(arg)
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.driver = driver
        if self.page_load_timeout:
            # Override default timeout
            self.driver.set_page_load_timeout(self.page_load_timeout)
        return
    
    def change_user_agent(self, user_agent: str):
        try:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        except AttributeError:
            logging.error('driver is None! Have you forgotten to open a browser instance?')
        
        return

    def get(self, url: str):
        if not self.driver:
            self.open_chromedriver()
        try:
            self.driver.get(url)
        except TimeoutException:
            error_msg = f"Page load timeout for url: {url}"
            logging.error(error_msg)
            raise TimeoutException(msg=error_msg)

    def wait_for_element(self, by: By, value: str, timeout: int = None, parent_element=None) -> Optional[WebElement]:
        if not parent_element:
            driver = self.driver
        else:
            driver = parent_element
        if not timeout:
            timeout = self.element_load_timeout
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            logging.error(f"Element with {by}='{value}' not found within {timeout} seconds.")
            return None

    def wait_for_elements(self, by: By, value: str, timeout: int = None, parent_element=None) -> Optional[List[WebElement]]:
        if not parent_element:
            driver = self.driver
        else:
            driver = parent_element
        if not timeout:
            timeout = self.element_load_timeout
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
            return driver.find_elements(by, value)
        except TimeoutException:
            logging.error(f"Element with {by}='{value}' not found within {timeout} seconds.")
            return None
        
    # Wait for element by tag, id, class, xpath
    def wfe_by_tag(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[WebElement]:
        return self.wait_for_element(by=By.TAG_NAME, value=value, timeout=timeout, parent_element=parent_element)
        
    def wfe_by_id(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[WebElement]:
        return self.wait_for_element(by=By.ID, value=value, timeout=timeout, parent_element=parent_element)
        
    def wfe_by_class(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[WebElement]:
        return self.wait_for_element(by=By.CLASS_NAME, value=value, timeout=timeout, parent_element=parent_element)
        
    def wfe_by_xpath(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[WebElement]:
        return self.wait_for_element(by=By.XPATH, value=value, timeout=timeout, parent_element=parent_element)
        
    def wfe_by_name(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[WebElement]:
        return self.wait_for_element(by=By.NAME, value=value, timeout=timeout, parent_element=parent_element)
    
    # Wait for multiple elements by tag, id, class, xpath
    def wfes_by_tag(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[List[WebElement]]:
        return self.wait_for_elements(by=By.TAG_NAME, value=value, timeout=timeout, parent_element=parent_element)
    
    def wfes_by_id(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[List[WebElement]]:
        return self.wait_for_elements(by=By.ID, value=value, timeout=timeout, parent_element=parent_element)
    
    def wfes_by_class(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[List[WebElement]]:
        return self.wait_for_elements(by=By.CLASS_NAME, value=value, timeout=timeout, parent_element=parent_element)
    
    def wfes_by_xpath(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[List[WebElement]]:
        return self.wait_for_elements(by=By.XPATH, value=value, timeout=timeout, parent_element=parent_element)
    
    def wfes_by_name(self, value: str, timeout: int = None, parent_element: Optional[WebElement] = None) -> Optional[List[WebElement]]:
        return self.wait_for_elements(by=By.NAME, value=value, timeout=timeout, parent_element=parent_element)

    def close_driver(self):
        if self.driver:
            self.driver.quit()
        self.driver = None


def create_ical(all_dates):
    cal = Calendar()
    for date_str in all_dates:
        date = parse(date_str).date()
        event = Event()
        event.name = "Unavailable"
        event.begin = datetime.combine(date, datetime.min.time())
        event.end = datetime.combine(date, datetime.min.time())
        cal.events.add(event)
    return cal


def save_ical_to_file(cal, filename):
    with open(filename, 'w') as f:
        f.writelines(cal)

# scraper = RootScraper(headless=False)

# scraper.get(base_url)

def go_to_next_month(scraper):
    btns = scraper.wfes_by_xpath('//button[@aria-disabled="false"]')
    btns[-1].click()
    
    
def go_to_previous_month(scraper):
    btns = scraper.wfes_by_xpath('//button[@aria-disabled="false"]')
    btns[0].click()


def collect_single_calendar_dates(scraper):
    temp_dates = []
    calendar_areas = scraper.wfes_by_xpath('//div[@data-testid="inline-availability-calendar"]')
    # TODO:: need a for loop through calendar_areas
    calendar_area = calendar_areas[0]
    tables = scraper.wfes_by_tag('tbody', parent_element=calendar_area)
    trs = scraper.wfes_by_tag('tr', parent_element=tables[1])
    for tr in trs:
        tds = scraper.wfes_by_tag('td', parent_element=tr)
        for td in tds:
            aria_disabled = td.get_attribute('aria-disabled')
            if aria_disabled and aria_disabled == 'true':
                td_div = scraper.wfe_by_tag('div', parent_element=td)
                the_date = td_div.get_attribute('data-testid')
                temp_dates.append(the_date.replace('calendar-day-', ''))
    return temp_dates


def automate_ical_link_creation(scraper, months_to_lookup):
    try:
        host_title = scraper.wfe_by_tag('h2').text
        host_description = scraper.wfe_by_tag('ol').text
    except:
        pass
    
    # close popup
    try:
        popup = scraper.wfes_by_xpath('//div[@role="dialog"]')
        if len(popup):
            popup[0].find_element(By.XPATH, './div').click()
            sleep(2)
    except:
        pass
    
    # Accesp cookies
    try:
        cookies_section = scraper.wfes_by_xpath('//div[@data-testid="main-cookies-banner-container"]')
        if len(cookies_section):
            btns = cookies_section[0].find_elements(By.TAG_NAME, 'button')
            if len(btns) == 2:
                btns[-1].click()
    except:
        pass
    # all_ical_links = []
    all_dates = []

    for i in range(months_to_lookup):
        sleep(3)
        dates = collect_single_calendar_dates(scraper)
        all_dates += dates
        if i < months_to_lookup - 1:
            go_to_next_month(scraper)

    cal = create_ical(all_dates)
    for i in range(months_to_lookup):
        sleep(0.5)
        if i < months_to_lookup - 1:
            go_to_previous_month(scraper)
    return cal.serialize()
