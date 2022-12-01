import os
import time
import re
import warnings
from datetime import datetime

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from pushnotifier import PushNotifier as pn

warnings.filterwarnings('ignore')
LAKAS_PAGE = 'https://ingatlan.com/szukites/kiado+lakas+tegla-epitesu-lakas+panel-lakas+ar-szerint+ix-ker+viii-ker+havi-140-ezer-Ft-ig'
pn = pn.PushNotifier(os.environ['PN_USER'], os.environ['PN_PASSWORD'], 'laki', os.environ['PN_API'])
maximum_price = 140000
devices = os.environ['PN_DEVICES'].split(':')

# Selenium script
options = Options()
options.add_argument("disable-infobars")
options.add_argument('--headless')
options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--remote-debugging-port=9222")  # this

seen_lakik = []


def check_lakik():
    # current lakik are empty, we are yet to see them
    global seen_lakik
    current_lakik = []

    # print what we are doing
    print(f'Checking lakis: {datetime.now().strftime("%Y/%M/%d - %H:%M")}')

    # make driver
    driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)
    driver.get(LAKAS_PAGE)

    # click agree on pop-up
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id=CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll]"))).click()
    except TimeoutException:
        print('No pop-up loaded')

    while True:
        # get the ads from the site
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "resultspage__listings")))
        elements = driver.find_elements(By.CLASS_NAME, "listing__card ")

        for element in elements:
            # wait for the page to be available
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "resultspage__container")))

            # get the price, if there is no price then skip
            try:
                price = int(re.sub(r'[^0-9]', '', element.find_element(By.CLASS_NAME, 'price').text))
            except:
                continue

            # is it within the price range
            if price < maximum_price:
                # get the url and scrape the laki id
                element_url = element.find_element(By.CLASS_NAME, 'listing__thumbnail').get_attribute('href')
                laki_id = element_url.split('/')[-1]

                # add it to the current lakik
                current_lakik.append(laki_id)

                # if there was no laki txt then do not send notification about every current laki
                # if we have not seen this laki sent notification
                if len(seen_lakik) and laki_id not in seen_lakik:
                    print(f'\tNew laki: {laki_id}')
                    pn.send_notification(f'Uj laki {int(price / 1000)}k-ert, ({element_url})', f'{element_url}', silent=False, devices=devices)

        # go to next page or exit
        page_buttons = driver.find_elements(By.CLASS_NAME, 'pagination__button')
        if page_buttons[-1].text == 'KÖVETKEZŐ OLDAL':
            page_buttons[-1].click()
        else:
            break

    # close the browser
    driver.close()

    # save current lakik to seen lakik
    seen_lakik = current_lakik


while True:
    check_lakik()
    time.sleep(5 * 60)  # wait 5 minute
