from termcolor import colored
def red(text): return colored(text, 'red')
def green(text): return colored(text, 'green')
def yellow(text): return colored(text, 'yellow')
def blue(text): return colored(text, 'blue')

ALL_STATUS = ['AVAILABLE', 'CHARGING', 'OUTOFORDER']
def available_filter(station): return station['stationStatus'] == ALL_STATUS[0]
def charging_filter(station): return station['stationStatus'] == ALL_STATUS[1]
def outoforder_filter(station): return station['stationStatus'] == ALL_STATUS[2]

def longitude(stations): return [st['longitude'] for st in stations]
def latitude(stations): return [st['latitude'] for st in stations]

def status_to_symbol(s):
    if s == ALL_STATUS[0]: return blue('_')
    elif s == ALL_STATUS[1]: return green('_')
    elif s == ALL_STATUS[2]: return red('_')
    else: assert False

charging_percent = lambda st: 100. * sum(map(lambda s : s[1] == ALL_STATUS[1], st[1])) / len(st[1])
outoforder_percent = lambda st: 100. * sum(map(lambda s : s[1] == ALL_STATUS[2], st[1])) / len(st[1])
charging_time = lambda st: sum(map(lambda s : s[1] == ALL_STATUS[1], st[1]))
def station_ranker(st):
    return charging_time(st)
    #return charging_percent(st) * (outoforder_percent(st) < 20)

hydfilter = lambda st: 17.2 < st['latitude'] < 17.6 and 78.4 < st['longitude'] < 78.6

def timestamp_compare(a, b):
    if a[0] != b[0]: return a[0] < b[0]
    elif a[1] != b[1]: return a[1] < b[1]
    elif a[2] != b[2]: return a[2] < b[2]
    elif a[3] != b[3]: return a[3] < b[3]
    elif a[4] != b[4]: return a[4] < b[4]
    else: return True
def timestamp_to_min(a):
    return a[4] + 60 * (a[3] + 24 * (a[2] + 30 * (a[1] + 12 * (a[0] - 2021))))
def timestamp_diff(a, b):
    if not timestamp_compare(a, b): a, b = b, a
    return timestamp_to_min(b) - timestamp_to_min(a)

month_name_to_num = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
day_names = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
