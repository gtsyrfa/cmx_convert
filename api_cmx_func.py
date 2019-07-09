#!/usr/bin/env python


import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
from copy import deepcopy


def get_content_json(
                      ipaddr="192.168.77.116",
                      username="admin",
                      password="Cisco!1",
                      rest_string="/api/location/v1/clients"):
    """This function download json from cmx_server. It not universal function"""
    restURL="HTTPS://"+ipaddr+rest_string
    # print("DEBUG>>"+restURL)
    # Disable certificate checking
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    request = requests.get(
        url=restURL,
        auth=HTTPBasicAuth(username, password),
        verify=False
    )
    # print("DEBUG>>"+ str(request.json()))
    return request.json()


def get_apmac_set(cmx_content: dict):
    """This function return unique mac addresses from ap's"""
    set_of_apmac = set()
    for i in range(len(cmx_content)):
        # We got set of ap's mac address
        set_of_apmac.update(
            {cmx_content[i]['statistics']['maxDetectedRssi']['apMacAddress']}
        )
    return set_of_apmac


def cnv_time_pulse(tmp_time):
    """This function convert time from ISO-8601 to Unix time"""
    # example of input time = "2019-07-03T12:48:26.150+0300" # it ISO 8601 format
    # example of output time = "1562158106"
    import datetime as dt 
    tmp_time = dt.datetime.strptime(tmp_time[:-9], "%Y-%m-%dT%H:%M:%S")
    tmp_time = round((tmp_time-dt.datetime(1970, 1, 1)).total_seconds())
    return tmp_time


def wifi_pulse_out(cmx_json_content: dict):
    tmpfile = {}
    for json_unit in cmx_json_content:
        # make variables from dict readable
        apmac = json_unit['statistics']\
            ['maxDetectedRssi']['apMacAddress'].replace(':', '-')
        cl_mac = json_unit['macAddress'].replace(':', '-')
        cl_rssi = json_unit['statistics']['maxDetectedRssi']['rssi']
        cl_time = cnv_time_pulse(json_unit['statistics']['lastLocatedTime'])
        ########
        # adding header if it none
        if apmac not in tmpfile:
            tmpfile.update(
                {apmac: {
                 "secret": "1",
                 "version": "1.0", "apmac": apmac,
                 "probe": []}}
            )
        ########
        # adding new record to dict
        tmpfile[apmac]["probe"].append({
            "macAddress": cl_mac,
            "rssi": cl_rssi,
            "timestamp_1": cl_time
        })
        ########
    return tmpfile


def make_safe(cmx_json_content: dict):
    """This function replace all mac addresses"""
    tmp_dict = deepcopy(cmx_json_content)
    for item in tmp_dict:
        item['macAddress'] = item['macAddress'].replace('x', 'y')
    return tmp_dict


def func_excepts(func):
    try:
        return func
    except requests.exceptions.RequestException as e:
        # print (f"We have problem witch function {func}")
        print(e)


# Decorate with functions for excepts
get_content_json = func_excepts(get_content_json)
get_apmac_set = func_excepts(get_apmac_set)
cnv_time_pulse = func_excepts(cnv_time_pulse)
wifi_pulse_out = func_excepts(wifi_pulse_out)
make_safe = func_excepts(make_safe)

if __name__ == "__main__":
    # If I haven't access to CMX server, I got content from file.
    # And I don't wont to make this logic :)
    # json_content = get_content_json()
    with open("father.json", 'r') as file_json:
        json_content = json.loads(file_json.read())
    safe_macs = make_safe(json_content)

    # Here I create a new dict that meets the requirements of the customer
    out_to_file = wifi_pulse_out(safe_macs)

    # I don't want any modification for father.json in test module
    with open("files/father.json", 'w') as file_json:
        json.dump(safe_macs, file_json, indent=4)

    keys = out_to_file.keys()
    for key in keys:
        with open(f"files/{key}.json", 'w') as file_json:
            json.dump(out_to_file[key], file_json, indent=4)
