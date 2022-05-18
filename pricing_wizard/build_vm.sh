scp scp -r Google\ Drive/My\ Drive/Dev/Pricing_automation/pricing_wizard ubuntu@ec2-18-196-64-252.eu-central-1.compute.amazonaws.com:/home/ubuntu
cd
vim .bashrc
## find last line and add
alias pr_wiz="python3 /home/ubuntu/pricing_wizard/CLI_code_setup.py"

sudo apt update
sudo apt install python3 python3-dev python3-venv
sudo apt-get upgrade
#apt-cache search wget
sudo apt install wget

wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py

## chrome and selenium

sudo apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

sudo -s dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get -fy install
google-chrome --version
##Google Chrome 97.0.4692.71 
pip3 install chromedriver-binary==98.0.4758.80


cp ./.local/lib/python3.8/site-packages/chromedriver_binary/chromedriver /home/ubuntu/pricing_wizard/.


pip3 install -r /home/ubuntu/pricing_wizard/requirements.txt
sudo apt install python3-testresources
pip3 install --upgrade google-api-python-client
pip3 install ipykernel
python3 -m ipykernel install --user


scp -i /Users/shikharsrivastava/Documents/ssh_keys/shikhar_pricing.pem -r Templates ubuntu@i-0b129d379bb8bb6fe:/home/ubuntu/.

#### testing selenium

import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.common.exceptions import TimeoutException ### for new wait for element functions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import selenium.webdriver.support.ui as ui
import time

path = r"/home/ubuntu/pricing_wizard/chromedriver"
#os.chdir(path)

ser = Service(path)

myoptions = webdriver.ChromeOptions()
myoptions.add_argument("--headless")
myoptions.add_argument("--disable-gpu")
myoptions.add_argument("window-size=1024,768")
myoptions.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=ser,options=myoptions)


def is_visible(locator, timeout):
    try:
        ui.WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
        return True
    except TimeoutException:
        return False


time.sleep(2)
driver.get("https://backoffice.getgrover.com/users/sign_in")
time.sleep(5)

is_visible("//*[@id='user_email']",timeout=10) 