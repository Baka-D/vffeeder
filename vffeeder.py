#!/usr/bin/python3
import sys

if sys.version_info < (3, 3):
    print('Your Python version doesn\'t meet the requirement, please upgrade your Python to 3.3 or above.')
    exit()

from time import sleep
import base64
import configparser
import socket
import urllib.parse
import urllib.request
import zlib
import logging

configLocation = '/etc/vffeeder.ini'
logLocation = '/var/log/vffeeder.log'

logging.basicConfig(filename = logLocation, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)

config = configparser.ConfigParser()

def get_help():
    print('Usage:')
    print('    vffeeder - Start feeding to VariFlight\'s server.')
    print('    vffeeder get - Print your current UUID.')
    exit()

def send_report(data):
    data = base64.b64encode(zlib.compress(data))
    try:
        urllib.request.urlopen(url = config.get('DEFAULT','reportURL'), data = urllib.parse.urlencode({'from': config.get('DEFAULT','uuid'), 'code': data}).encode('ascii'))
    except Exception as e:
        logging.critical('Failed to contact with VariFlight feed server.', exc_info = True)
        print('Failed to contact with feed server.')

def get_uuid():
    config.read(configLocation)
    feederUuid = config.get('DEFAULT','uuid')
    print(feederUuid)
    exit()

def get_report():
    config.read(configLocation)
    HOST = config.get('HOST_INFO','address')
    PORT = int(config.get('HOST_INFO','port'))
    logging.info('Vffeeder started!')

    while True:
        while True:
            try:
                s = socket.create_connection((HOST, PORT))
                break
            except Exception as e:
                logging.critical('Failed to reach dump1090, please check your Internet connection.', exc_info = True)
                print('Failed to reach dump1090, please check your Internet connection, will try again in 10s.')
                sleep(10)
        data = s.recv(1024)
        send_report(data)

if len(sys.argv) == 1:
    get_report()
elif sys.argv[1] == 'help':
    get_help()
elif sys.argv[1] == 'get':
    get_uuid()
else:
    print('Invalid argument.\n    use \'vffeeder help\' to get command list.')