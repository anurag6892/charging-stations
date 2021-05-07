#!/opt/local/bin/python

from twython import Twython
import subprocess, datetime
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
from tokens import *

def post_to_twitter(name, latitude, longitude, kw=0, extra_text=""):
    if int(kw) > 0: status = 'New %sKW CCS2 fast charger at ' % (kw)
    else: status = 'New CCS2 fast charger at '
    status += name
    status += '\nhttps://www.google.com/maps/search/?api=1&query=%f,%f' % (latitude, longitude)
    if len(extra_text): status = extra_text + '.\n' + status

    twitter_client = Twython(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    print(status)
    twitter_client.update_status(status=status)

def send_email(name, latitude, longitude, date_added):
    msg = EmailMessage()
    content = name
    content += '\n' + latitude + ',' + longitude
    content += '\nDate added ' + date_added
    content += '\nhttps://www.google.com/maps/search/?api=1&query=%s,%s' % (latitude, longitude)
    msg.set_content(content)

    msg['Subject'] = 'New Tata Power Charger'
    msg['From'] = 'anurag6892@gmail.com'
    msg['To'] = 'anurag6892@gmail.com'
    gmail_user = 'anurag6892@gmail.com'
    gmail_password = GMAIL_TOKEN

    try:
        s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        s.ehlo()
        s.login(gmail_user, gmail_password)
    except:
        print("Something went wrong while logging in")
        return
    try:
        s.send_message(msg)
    except:
        print("Something went wrong while sending message")
        return
    s.quit()

logFileName = lambda d : 'logs/station-locations-%d-%02d-%02d' % (d.year, d.month, d.day)

last_proc = open('last-proc.txt', 'r').read().strip().split('-')
last_proc = datetime.datetime(int(last_proc[0]), int(last_proc[1]), int(last_proc[2]))
today = datetime.datetime.today()
today = datetime.datetime(today.year, today.month, today.day)
assert(today >= last_proc)
cur = last_proc + datetime.timedelta(days=1)
prev = last_proc

while cur < today:
    file1, file2 = logFileName(cur), logFileName(prev)
    prev, cur = cur, cur + datetime.timedelta(days=1)

    output = subprocess.Popen('diff '+ file1 + "   " + file2, shell=True, stdout=subprocess.PIPE)
    output = output.stdout.read().decode('utf-8')
    if len(output) >= 8:
        for line in output.splitlines()[7:]:
            if line[0] == '<':
                print("Added line")
                print(line[2:])
                name, loc = line[2:].split(' : ')
                lat, lng = loc.split(',')
                name = name.replace('_', ' ')
                send_email(name, lat, lng, '%d-%02d-%02d' % (cur.year, cur.month, cur.day));
                #real_name = input("Provide full address for %s:\n" % (name))
                #if len(real_name) == 0: continue
                #kw = input("Provide KW: ")
                #extra_text = input("Anything about the station: ")
                #post_to_twitter(real_name, float(lat), float(lng), kw, extra_text)
            elif line[0] == '>':
                print("Removed line")

open('last-proc.txt', 'w').write('%d-%d-%d' % (prev.year, prev.month, prev.day))

def get_location_name(lat, lng):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    #options.add_argument('--headless')
    driver = webdriver.Chrome(executable_path = '/Users/anurag/Downloads/charging-stations/chromedriver', chrome_options=options)

    url = 'https://www.latlong.net/Show-Latitude-Longitude.html'
    driver.get(url)
    driver.find_element_by_name('latitude').send_keys(str(lat))
    driver.find_element_by_name('longitude').send_keys(str(lng))
    time.sleep(2)
    box = driver.find_element_by_name('lltoken') #'Show Lat Long converted address on Map')
    button = driver.find_element_by_css_selector('button.margin38')
    button.click()
    time.sleep(2)
    source = driver.page_source
    soup = BeautifulSoup(source, 'html.parser')
    div = soup.find('bgw shadow padding10')
    print(div)
    driver.close()
    return ""

