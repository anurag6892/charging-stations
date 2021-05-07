#!/opt/local/bin/python

from common import *
from selenium import webdriver
from bs4 import BeautifulSoup
import argparse, os, time, ast, json
from datetime import datetime

parser = argparse.ArgumentParser(description='')
parser.add_argument('--prefix', type=str, default='test-logs/')
parser.add_argument('--printLocations', action='store_true', default=False)
parser.add_argument('--printStatus', action='store_true', default=False)
args = parser.parse_args()

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')

WAIT_TIME = 5

def get_ccs2_stations():
    driver = webdriver.Chrome(executable_path = '/Users/anurag/Downloads/charging-stations/chromedriver', options=options)
    driver.get('https://ezcharge.tatapower.com/evselfcare/#/home')
    time.sleep(WAIT_TIME)
    filter_button = driver.find_element_by_id('mapFilterButton')
    filter_button.click()
    time.sleep(WAIT_TIME)
    connectors = driver.find_elements_by_class_name('connector-label')
    ccs2 = connectors[3]
    ccs2.click()
    time.sleep(WAIT_TIME)

    all_buttons = driver.find_elements_by_class_name('col-md-6')
    for button in all_buttons:
        if button.text == "Apply":
            button.click()
    time.sleep(WAIT_TIME)
    source = driver.page_source
    driver.close()
    return source

source = get_ccs2_stations()

soup = BeautifulSoup(source, 'html.parser')
div = soup.find('app-map-view')
stations = div.find('div', class_='d-none').get_text()
stations = stations.replace(']', '').replace('[', '').strip()
delim = '},'
if len(stations) == 0:
    print('Empty stations, exiting')
    exit(1)
stations = [st + delim[0] for st in stations.split(delim) if st[-1] != '}']
stations = [json.loads(station) for station in stations]

if args.printLocations:
    f = open(args.prefix + '/station-locations-%s' % (datetime.today().strftime('%Y-%m-%d')), 'w')
    time = datetime.now()
    f.write('%d-%d-%d-%d-%d\n' % (time.year, time.month, time.day, time.hour, time.minute))
    f.write("Stations Total:%d\n" % (len(stations)))
    for station in stations:
        f.write("%s : %s,%s\n" % (station['stationCode'], station['latitude'], station['longitude']))
    f.close()

if args.printStatus:
    available = list(filter(available_filter, stations))
    charging = list(filter(charging_filter, stations))
    outoforder = list(filter(outoforder_filter, stations))

    f = open(args.prefix + '/ez-charge-%s' % (datetime.today().strftime('%Y-%m-%d')), 'a')
    time = datetime.now()
    f.write('%d-%d-%d-%d-%d\n' % (time.year, time.month, time.day, time.hour, time.minute))
    f.write("Stations Total:%d Available:%d Charging:%d Outoforder:%d\n" % (len(stations), len(available), len(charging), len(outoforder)))
    for station in stations:
        f.write("%s : %s\n" % (station['stationCode'], station['stationStatus']))
    f.close()
