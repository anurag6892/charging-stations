#!/Users/anurag/Downloads/work/bin/python

import argparse, os, time, json
from joblib import Memory
from common import *
from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt
import numpy as np
import mplleaflet
import datetime, subprocess

parser = argparse.ArgumentParser(description='')
parser.add_argument('-c', '--clearCache', action='store_true', default=False)
parser.add_argument('-d', '--date', type=str, nargs='+', default=[])
parser.add_argument('-s', '--startHour', type=int, default=0)
parser.add_argument('-e', '--endHour', type=int, default=24)
parser.add_argument('-H', '--histogram', action='store_true', default=False)
parser.add_argument('-t', '--timeseries', action='store_true', default=False)
parser.add_argument('-S', '--summary', action='store_true', default=False)
parser.add_argument('-m', '--map', action='store_true', default=False)
parser.add_argument('--day', type=str, nargs='+', default=day_names)
args = parser.parse_args()

memory = Memory(location='./cron-parse-cachedir', verbose=0)
if args.clearCache: memory.clear()

EPOCH, MAX_CHARGING_TIME = 5, 95 # Minutes

def parse_timestamp(line):
    elems = line.split(' ')
    if len(elems) > 1: # Old version: Linux date
        year, month, date, time_ = elems[-1], elems[1], elems[2], elems[3]
        month = month_name_to_num.index(month)
        assert month != -1
        hour, minute = time_.split(':')[:2]
    else: # New version: Python date
        year, month, date, hour, minute = line.split('-')
    return (int(year), int(month), int(date), int(hour), int(minute))

@memory.cache
def parse_log(base_path, final_files):
    print("Processing files : ", final_files)
    all_data = []
    for filename in final_files:
        cur_timestamp = ''
        f = open(join(base_path, filename), 'r')
        lines = f.read().split('\n')[:-1]
        for line in lines:
            if line.find('2021') != -1: # Start of new timestamp
                cur_timestamp = parse_timestamp(line)
            elif len(line.split(' : ')) == 2:
                station, status = line.split(' : ')
                all_data += [(cur_timestamp, station, status)]
    return all_data

base_path = 'logs'
allfiles = [f for f in listdir(base_path) if isfile(join(base_path, f))]
ezcharge_files = [f for f in allfiles if f.find('ez-charge') != -1]
print(args.date)
if len(args.date) == 0:
    today = datetime.datetime.today()
    args.date = ['%d-%02d-%02d' % (today.year, today.month, today.day)]
if args.date[0] == 'all': final_files = ezcharge_files
else:
    date_match = lambda f, d : f.find(d) != -1
    final_files = [f for f in ezcharge_files if sum(map(lambda d : date_match(f, d), args.date))]
assert len(final_files) >= 1

def select_date_from_day(filename):
    year, month, day = filename.split('-')[2:]
    date = datetime.datetime(int(year), int(month), int(day))
    day = day_names[date.weekday()]
    return day in args.day
final_files = list(filter(select_date_from_day, final_files))

all_data = parse_log(base_path, final_files)
all_data = sorted(all_data, key=lambda a : timestamp_to_min(a[0]))
all_data = list(filter(lambda s : args.startHour <= s[0][3] < args.endHour, all_data))

station_data = {}
for datapoint in all_data:
    time_, station, status = datapoint
    assert status in ALL_STATUS
    if station in station_data.keys(): station_data[station] += [(time_, status)]
    else: station_data[station] = [(time_, status)]

for station in station_data.keys():
    status_list = station_data[station]
    prev_epoch_charging, epoch_length = False, 0
    for i, status in zip(range(len(status_list) + 1), status_list + [None]):
        if status is not None and status[1] == 'CHARGING':
            if prev_epoch_charging: epoch_length += 1
            else: prev_epoch_charging, epoch_length = True, 1
        else:
            if status is None: assert i == len(status_list)
            if prev_epoch_charging:
                epoch_time = timestamp_diff(status_list[i-1][0], status_list[i- epoch_length][0]) + 5
                if epoch_time > MAX_CHARGING_TIME:
                    for j in range(epoch_length):
                        status_list[i-1-j] = (status_list[i-1-j][0], 'AVAILABLE')
            prev_epoch_charging, epoch_length = False, 0

    station_data[station] = status_list

# Sanitize
station_data = dict(filter(lambda item: len(item[1]) > 5, station_data.items()))
station_data = {key.replace('_Charging_Station', '') : val for key, val in station_data.items()}
station_data = dict(list(sorted(station_data.items(), key=station_ranker, reverse=True)))

all_charging_sessions = []
status_breakdown = []

for station in station_data.keys():
    status_list = station_data[station]
    #vals = [100. * len(list(filter(lambda s : s[1] == status, status_list))) / len(status_list) for status in ALL_STATUS]
    vals = [len(list(filter(lambda s : s[1] == status, status_list))) * EPOCH for status in ALL_STATUS]
    if vals[1] > 0:
        status_breakdown += [(vals[0], vals[1], vals[2])]
        prev_epoch_charging, epoch_length = False, 0
        charging_sessions = []
        for i, status in zip(range(len(status_list)+1), status_list + [None]):
            if status is not None and status[1] == 'CHARGING':
                if prev_epoch_charging: epoch_length += 1
                else: prev_epoch_charging, epoch_length = True, 1
            else:
                if prev_epoch_charging:
                    charging_sessions += [timestamp_diff(status_list[i-1][0], status_list[i-epoch_length][0]) + EPOCH]
                prev_epoch_charging, epoch_length = False, 0
        all_charging_sessions += [charging_sessions]
    else:
        status_breakdown += [None]
        all_charging_sessions += [None]

if args.histogram:
    hour_charging, hour_total = np.zeros(24), np.zeros(24)
    for _, station in zip(range(50), station_data.keys()):
        status_list = station_data[station]
        for time_, status in status_list:
            hour_total[time_[3]] += EPOCH
            if status == 'CHARGING': hour_charging[time_[3]] += EPOCH
    hour_util = [100. * a / b  for a, b in zip(hour_charging, hour_total)]
    hour_util = hour_util[6:-1] + hour_util[:6]
    xlabels = ['6am', '9am', '12pm', '3pm', '6pm', '9pm', '12am', '3am']
    #ind = [x + 0.5 for x in range(len(hour_util))]
    plt.plot(hour_util)
    plt.xticks(range(0, 24, 3), xlabels)
    plt.xlabel('Hour')
    plt.ylabel('Utilization (%)')
    plt.title('Hourly utilization distribution')
    #plt.xlim(xmin=ind[0] - 0.5, xmax=ind[-1] + 0.5)
    plt.xlim(xmin=0, xmax=23)
    plt.grid(True)
    plt.show()
    plt.close()
    exit(1)


    flat_list = [item for sublist in all_charging_sessions if sublist is not None for item in sublist]
    print('Total charging sessions %d' % (len(flat_list)))
    plt.hist(flat_list, 19, density=1, facecolor='green', alpha=0.75)
    plt.xlabel('Session Length (min)')
    plt.ylabel('Count')
    plt.xlim(xmin=EPOCH, xmax=MAX_CHARGING_TIME)
    plt.title('Histogram of %d charging sessions' % (len(flat_list)))
    plt.grid(True)
    #plt.show()
    plt.close()

    status_breakdown = list(filter(lambda s : s is not None,  status_breakdown))
    print('Total stations %d' % (len(status_breakdown)))
    avail = [a[0] for a in status_breakdown]
    charge = [a[1] for a in status_breakdown]
    outoforder = [a[2] for a in status_breakdown]
    ind = range(len(avail))
    plt.bar(ind, avail, width=1, label='Available', color='g')
    plt.bar(ind, outoforder, width=1, bottom=avail, label='Outoforder', color='r')
    plt.bar(ind, charge, width=1, bottom=[a + b for a, b in zip(avail, outoforder)], label='Charging', color='b')
    plt.xlabel('Station id')
    plt.ylabel('Percentage')
    plt.xlim(xmin=ind[0], xmax=ind[-1])
    plt.title('%d charging sessions' % (len(flat_list)))
    #plt.show()
    plt.close()

    utilization = [val[1] for val in status_breakdown]
    plt.bar(range(len(utilization)), utilization)
    plt.ylabel('Charging time (minutes)')
    plt.xlabel('Station')
    plt.title('Histogram of %d stations' % (len(utilization)))
    plt.grid(True)
    plt.show()
    plt.close()

if args.summary:
    for i, station in zip(range(min(100, len(station_data))), station_data.keys()):
        if status_breakdown[i] is None: continue
        vals = status_breakdown[i]
        charging_sessions = all_charging_sessions[i]
        if len(charging_sessions):
            print(station, blue("%d" % (vals[0]+0.5)), green("%d" % (vals[1]+0.5)), red("%d" % (vals[2]+0.5)), "Sessions: %d Time: %d" % (len(charging_sessions), sum(charging_sessions)))

if args.timeseries:
    for i, station in zip(range(len(station_data)), station_data.keys()):
        if status_breakdown[i] is None: continue
        vals = status_breakdown[i]
        charging_sessions = all_charging_sessions[i]
        if len(charging_sessions):
            print(station, blue("%d" % (vals[0]+0.5)), green("%d" % (vals[1]+0.5)), red("%d" % (vals[2]+0.5)))
            print("Sessions: %d Charging Time: %d List: %s" % (len(charging_sessions), sum(charging_sessions), (' ').join(map(str, charging_sessions))))
            print_str = ''
            prev_day, prev_hour = -1, -1
            print_flag = True
            for time_, status in station_data[station]:
                #if status != 'CHARGING': continue
                cur_day, cur_hour = time_[2], time_[3]
                print_day = prev_day != cur_day
                print_hour = prev_hour != cur_hour # and int(prev_hour/6) != int(cur_hour/6)
                if print_flag:
                    if print_day:
                        print_flag = False
                        if prev_day != -1: print_str += '\n'
                        print_str += "%d-%d " % (time_[1], time_[2])
                    if print_hour:
                        print_flag = False
                        print_str += str(time_[3])
                if True or status == 'CHARGING':
                    print_flag = True
                    print_str += status_to_symbol(status)
                prev_day, prev_hour = cur_day, cur_hour
            print(print_str)

if args.map:
    ps = subprocess.Popen(('ls', '-Art', 'logs'), stdout=subprocess.PIPE)
    ps.wait()
    ps = subprocess.Popen(['grep', 'station-locations'], stdin=ps.stdout, stdout=subprocess.PIPE)
    output = subprocess.check_output(['tail', '-n', '1'], stdin=ps.stdout).decode('utf-8')
    ps.wait()
    f = open('logs/' + output.strip(), 'r')
    text = f.read()
    text = text.replace(']', '').replace('[', '').strip()
    delim = '},'
    stations = text.split('\n')[2:]
    station_locations = {}
    for station in stations:
        name, loc = station.split(' : ')
        station_locations[name.replace('_Charging_Station', '')] = (float(loc.split(',')[0]), float(loc.split(',')[1]))

    for num in [10]:
        top_stations = list(station_data.keys())[num-10:num]
        print(top_stations)
        fig, ax = plt.subplots()
        for i in range(len(top_stations)):
            latitude, longitude = station_locations[top_stations[i]]
            ax.scatter(longitude, latitude, s = pow(status_breakdown[i][1], 1.5))
        ax.set_title('Top %d stations for %s' % (num, ' '.join(final_files)))
        mplleaflet.show(fig=fig)
        plt.close()
