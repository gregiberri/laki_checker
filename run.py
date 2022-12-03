import os
import time
import re
import warnings
from datetime import datetime
from tqdm import tqdm

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
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

current_lakik = []

if not os.path.exists('lakik.txt'):
    did_lakistxt_exist = False
    file = open('lakik.txt', 'w')
    file.close()


def check_lakik():
    global did_lakistxt_exist

    # print what we are doing
    print(f'Checking lakis: {datetime.now().strftime("%Y/%M/%d - %H:%M")}')

    # load laki names we have seen
    with open('lakik.txt', 'r') as f:
        seen_lakik = f.read().splitlines()

    # make driver
    driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)
    driver.get(LAKAS_PAGE)

    # click agree on pop-up
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id=CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll]"))).click()
    except TimeoutException:
        print('No pop-up loaded')

    page = 0
    while True:
        # get the ads from the site
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "resultspage__listings")))
        elements = driver.find_elements(By.CLASS_NAME, "listing__card ")

        page += 1
        print(f'Checking page: {page}')
        for element in tqdm(elements):
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

                # if we have not seen this laki sent notification
                if laki_id not in seen_lakik:
                    print(f'\tNew laki: {laki_id}')
                    if did_lakistxt_exist:
                        pn.send_notification(f'Uj laki {int(price / 1000)}k-ert,    \n{element_url}', f'{element_url}', silent=False, devices=devices)

        # go to next page or exit
        page_buttons = driver.find_elements(By.CLASS_NAME, 'pagination__button')
        if page_buttons[-1].text == 'KÖVETKEZŐ OLDAL':
            page_buttons[-1].click()
        else:
            break

    # close the browser
    driver.close()

    # save currently available lakis
    with open('lakik.txt', 'w') as f:
        for laki in current_lakik:
            f.write(f"{laki}\n")
        did_lakistxt_exist = True


while True:
    check_lakik()
    print('Waiting for 5 minutes.')
    time.sleep(5 * 60)  # wait 5 minute
