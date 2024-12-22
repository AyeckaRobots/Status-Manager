import time

import json
import requests
import logging
import keyboard
from datetime import datetime

import threading


def get_auth(username, password, ip):
    try:
        response = requests.post(f"http://{ip}/api/login", json={"username": username, "password": password})
    except TimeoutError as e:
        print(f"couldn't connect to ip: {ip} ")
        return -1
    
    return f"Bearer {response.json()['token']}"


def get_advanced_stats(token, ip):
    try:
        data = requests.get(f"http://{ip}/api/advanced_status", headers={'Authorization': token})
    except TimeoutError as e:
        print(f"No response from {ip}, error: {e}")
        return -1

    return data.json()["agg_slices"][0]


def read_esno():

    # Open and read the JSON file
    with open("esno.json", 'r') as file:
        data = json.load(file)

    print(data)


def log_stats(info, current_bit_rate, current_esno, current_frame_counter):
    global current_missed_counter
    
    if info["bit_rate"] != current_bit_rate:
        logging.info(f"Got new bit rate of: {info['bit_rate']}")
    # if 9 > current_esno > 11:
    #     logging.error(f"Esno value out of range: {current_esno}")
    if current_frame_counter > info["frame_counter"]:
        logging.info("Got new frames")
    if current_missed_counter - info["offset"] > info["missed_counter"]:
        logging.warning(f"Missed frames! amount: {current_missed_counter - info['missed_counter'] - info['offset']}, esno: {current_esno}")


def start_logging(ip):
    global current_missed_counter
    
    username = "admin"
    password = "admin"

    token = get_auth(username, password, ip)
    print(f"got token: {token}")

    if token == -1:
        print("No connection established. exiting program.")
        return
    
    info = {"frame_counter":0 , "missed_counter":0 , "bit_rate":0 , "esno":0, "offset":0}
    
    threading.Thread(target=inputs, args=[info]).start()

    while True:
        print("sending req (press 'i' for info, 'r' to reset missed)")
        agg = get_advanced_stats(token, ip)

        if agg == -1:
            continue

        # this is theoretical from here on out. needs testing for agg response.
        current_bit_rate = agg['bit_rate']
        current_esno = agg['esno']  # string (no decimal point, needs division by 10)
        current_frame_counter = agg['frame_counter']
        try:
            current_missed_counter = agg['missed_counter']
        except KeyError as e:
            current_missed_counter = 0
            
        current_esno = int(current_esno) / 10

        log_stats(info, current_bit_rate, current_esno, current_frame_counter)
        
        info["frame_counter"] = current_frame_counter
        info["missed_counter"] = current_missed_counter - info["offset"]
        info["bit_rate"] = current_bit_rate
        info["esno"] = current_esno
        
        time.sleep(10)

            
def inputs(info: dict):
    
    while True:
        if keyboard.is_pressed('i'):
            print(f"-----------------------------------------------\nCard Activity Report {datetime.today().strftime('%H:%M:%S')}")
            print(f"Status:\nCurrent frame: {info['frame_counter']}\nAmount missed: {info['missed_counter']}\nCurrent esno {info['esno']}")
            print("-----------------------------------------------")
            time.sleep(1)
        if keyboard.is_pressed('r'):
            info.update({"missed_counter":0})
            info.update({"offset": current_missed_counter})
            time.sleep(1)

def main():
    ipaddress = input("Enter the ip of the device. (just press enter for 192.168.10.200)")
    if ipaddress == '':
        ipaddress = "192.168.10.200"
    start_logging(ipaddress)


if __name__ == "__main__":
    
    current_missed_counter = 0

    # read_esno()
    logging.basicConfig(filename="newfile.log",
                        format='%(asctime)s %(message)s',
                        filemode='w')
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)  # change warning to info to include frame and bit-rate changes.

    main()
