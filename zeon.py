#!/opt/local/bin/python

from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
driver = webdriver.Chrome(executable_path = '/Users/anurag/Downloads/charging-stations/chromedriver', chrome_options=options)

# Charging locations
url = 'http://www.zeoncharging.com/charging-locations'
driver.get(url)

location_map = driver.find_element_by_class_name('location-map')
#iframes = driver.find_elements_by_tag_name('iframe')
#for iframe in iframes: print(iframe)
page_source = driver.page_source

maps_link = 'https://www.google.com/maps/d/embed?mid=1rsYILd39XGYkxIv_3bWRY2BU6ighul76&hl=en&ll=11.643155026044692%2C77.08910483437501&z=8'

# Contact form
#url = 'http://www.zeoncharging.com/contactus.php'
#driver.get(url)

#driver.find_element_by_name('name').send_keys('ABCD')
#driver.find_element_by_name('phone').send_keys('1234567890')
#driver.find_element_by_name('email').send_keys('me@gmail.com')
#driver.find_element_by_name('msg').send_keys('Hello')
##captcha_text = input("enter captcha text: ")
#driver.find_element_by_name('captcha').send_keys('12345') # Let captcha fail
#driver.find_element_by_class_name('ripple').click()
