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
import uuid
import zlib
import os
import signal
import logging

cronfileLocation = '/etc/cron.d/vffeeder'
configLocation = '/etc/vffeeder.ini'
pidLocation = '/var/lib/vffeeder/vffeeder.pid'
logLocation = '/var/lib/vffeeder/vffeeder.log'

logging.basicConfig(filename = logLocation, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)

config = configparser.ConfigParser()

class Register:
    def check(self):
        try:
            config.read(configLocation)
            nodeUUID = config.get('DEFAULT','uuid')
        except:
            self.signup()
        confirmInput = input('It seems that you already have a configration file for VariFlight feeder, would you like to override that file? (y/N)')[:1]
        if confirmInput == 'n' or confirmInput == '' or confirmInput == 'N':
            os.system('/bin/systemctl enable vffeeder')
            print('Your UUID for current configuration is', nodeUUID+'. You could run \'systemctl start vffeeder\' to start feed data now!')
        else:
            self.signup()

    def signup(self):
        while True:
            while True:
                self.address = input('Please enter your existing dump1090\'s IP address(could be \'localhost\' if it\'s installed on the same machine with the feeder).\nIP address:')
                self.attr = 'address'
                if self.validate() == True:
                    break
                else:
                    print('Invalid IP address, please check again and re-enter.')
            while True:
                self.port = input('Please enter your existing dump1090\'s port number(should be 30003 for most installations).\nPort number:')
                self.attr = 'port'
                if self.validate() == True:
                    break
                else:
                    print('Invalid port number, please check again and re-enter.')
            while True:
                self.nodeUUID = input('Please enter your UUID if this is an existing feeder, leave it blank if this is a new feeder.\nFeeder UUID:')
                self.attr = 'uuid'
                if self.validate() == True:
                    break
                else:
                    print('Invalid UUID, please check again and re-enter.')
            confirmInput = input('Is the above information correct? [Y/n]')[:1]
            if confirmInput == 'y' or confirmInput == '' or confirmInput == 'Y':
                if self.connection_test() == False:
                    print('Your network connection with the provided dump1090 address is not established, please check again.')
                else:
                    break
            else:
                print('Please enter your information again.\n')
        self.write_config()
        print('VariFlight feeder has been installed successfully, please run \'systemctl start vffeeder\' to start feeding!')
        exit()

    def validate(self):
        if self.attr == 'address':
            if self.address == 'localhost':
                self.address = '127.0.0.1'
                return True
            else:
                try:
                    for i in self.address.split('.'):
                        if i.isdigit() and int(i) in range(0,255):
                            return True
                        else:
                            raise ValueError()
                except:
                    return False
        elif self.attr == 'port':
            if self.port.isdigit() and int(self.port) in range(1,65534):
                return True
            else:
                return False
        elif self.attr == 'uuid':
                if self.nodeUUID == '' or len(self.nodeUUID) == 16:
                    if self.nodeUUID == '':
                        data = uuid.uuid4().hex[16:]
                        print('Your new UUID is', data+'. Please register this UUID on http://flightadsb.variflight.com/share-data/script to improve the accuracy of the data you feed to us.')
                        self.nodeUUID = data
                    return True
                else:
                    return False

    def connection_test(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.address, int(self.port)))
            except Exception as e:
                logging.error('Failed to contact with dump1090 with provided data during signup.', exc_info = True)
                return False
            s.close()
            return True

    def write_config(self):
        config.read(configLocation)
        config.set('DEFAULT','uuid',self.nodeUUID)
        config.set('DEFAULT','reportURL','http://adsb.feeyo.com/adsb/ReceiveCompressADSB.php')
        config.set('HOST_INFO','address',self.address)
        config.set('HOST_INFO','port',self.port)
        with open(configLocation, 'w') as configfile:
            config.write(configfile)
            configfile.close()
        os.system('/bin/systemctl enable vffeeder')
        confirmInput = input('Would you like to enable auto-update for vffeeder? You will need to manually update it if auto-update is disabled. [Y/n]')[:1]
        if confirmInput == 'y' or confirmInput == '' or confirmInput == 'Y':
            updateCommand = '0 0 * * * root /usr/local/bin/vffeeder update >> /var/log/vffeeder-update.log\n'
            try:
                with open(cronfileLocation, 'w') as cronjob:
                    cronjob.write(updateCommand)
                    cronjob.close()
                os.chmod(cronfileLocation, 0o644)
            except:
                logging.error('Failed to add cronjob.', exc_info=True)
                print('Failed to add cronjob, please add the following line to your cronjob file manually.')
                print(updateCommand)

class Update:
    def check(self):
        logging.info('Checking updates...')
        if parse_version(currentVersion) < parse_version(latestVersion):
            logging.info('New version found! Updating...')
            self.upgrade()
        logging.info('This is the latest version, no need to update.')
        print('This is the latest version, no need to update.')
        exit()

    def upgrade(self):
        scriptLocation = os.path.abspath(__file__)
        latestScript = getIni
        self.setFinalizeState()
        with open(scriptLocation, 'w') as scriptFile:
            scriptFile.write(latestScript)
            scriptFile.close()
        os.kill(get_pid(), signal.SIGKILL)
        exit()

    def setFinalizeState(self):
        config.set('DEFAULT','updateFinalized','False')
        with open(configLocation, 'w') as configFile:
            config.write(configLocation)
            config.close()
        exit()

    def finalize(self):
        config.read(configLocation)
        config.set('DEFAULT','version',latestVersion)
        config.set('DEFAULT','updateFinalized','True')
        with open(configLocation, 'w') as configfile:
            config.write(configfile)
            configfile.close()
        logging.info('Update completed successfully!')
        print('Update completed successfully!')

def parse_version(data):
    versionFull = data.split('.')
    version = ()
    for versionNumber in versionFull:
        version = version + (versionNumber,)
    return version

def get_help():
    print('Usage:')
    print('    vffeeder - Start feeding to VariFlight\'s server')
    print('    vffeeder update - Check and update to the latest version of vffeeder')
    print('    vffeeder signup - Configure and setup vffeeder')
    exit()

def send_report(data):
    data = base64.b64encode(zlib.compress(data))
    try:
        urllib.request.urlopen(url = config.get('DEFAULT','reportURL'), data = urllib.parse.urlencode({'from': config.get('DEFAULT','uuid'), 'code': data}).encode('ascii'))
    except Exception as e:
        logging.critical('Failed to contact with VariFlight feed server.', exc_info = True)
        print('Failed to contact with feed server.')

def create_pid():
    processPid = str(os.getpid())
    with open(pidLocation, 'w') as pid_file:
        pid_file.write(processPid)
        pid_file.close()

def get_pid():
    with open(pidLocation, 'r') as pid_file:
        processPid = int(pid_file.read())
        pid_file.close()
    return processPid

def get_report():
    create_pid()
    config.read(configLocation)
    HOST = config.get('HOST_INFO','address')
    PORT = int(config.get('HOST_INFO','port'))

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

try:
    getIni = urllib.request.urlopen(url = 'https://raw.githubusercontent.com/Baka-D/vffeeder/master/vffeeder.ini').read().decode()
    latestVersion = getIni.split('\n')[1].split(' ')[2]
    if os.path.isfile(configLocation) == False:
        with open(configLocation, 'w') as config_file:
            config_file.write(getIni)
            config_file.close()
    config.read(configLocation)
    currentVersion = config.get('DEFAULT','version')
    if parse_version(currentVersion) == parse_version(latestVersion):
        if config.get('DEFAULT','updateFinalized') == 'False':
            Update().finalize()
        logging.info('vffeeder started successfully!')
except Exception as e:
    logging.error('Failed to fetch latest configuration file.', exc_info = True)
    print('Failed to fetch latest configuration file.')

if len(sys.argv) == 1:
    get_report()
elif sys.argv[1] == 'signup':
    Register().check()
elif sys.argv[1] == 'update':
    Update().check()
elif sys.argv[1] == 'help':
    get_help()
else:
    print('Invalid argument.\n    use \'vffeeder help\' to get command list.')