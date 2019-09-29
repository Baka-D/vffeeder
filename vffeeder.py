#!/usr/bin/python3
import sys

try:
    assert sys.version_info >= (3, 3)
except AssertionError:
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

configLocation = '/etc/vffeeder.ini'

config = configparser.ConfigParser()

class Register:
    def check(self):
        try:
            open(configLocation, 'r').close()
        except FileNotFoundError:
            self.signup()
        confirmInput = input('It seems that you already have a configration file for Variflight feeder, would you like to override that file? (Y/n)')[:1]
        if confirmInput == 'y' or confirmInput == '' or confirmInput == 'Y':
            self.signup()
        else:
            config.read(configLocation)
            try:
                nodeUUID = config.get('DEFAULT','uuid')
            except:
                print('Invalid file format, please check your configuration file again.')
                exit()
            os.system('/bin/systemctl enable vffeeder')
            print('Your UUID for current configuration is', nodeUUID+'. You could run \'systemctl start vffeeder\' to start feed data now!')

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
                    print('Your UUID is', self.nodeUUID+', please register it on http://flightadsb.variflight.com/share-data/script if you haven\'t yet.')
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
        print('Variflight feeder has been installed successfully, please run \'systemctl start vffeeder\' to start feeding!')
        exit()

    def validate(self):
        if self.attr == 'address':
            if self.address == 'localhost':
                return True
            else:
                a = self.address.split('.')
                if len(a) != 4:
                    return False
                for x in a:
                    if not x.isdigit():
                        return False
                    i = int(x)
                    if i < 0 or i > 255:
                        return False
                return True
        elif self.attr == 'port':
            if not self.port.isdigit():
                return False
            elif int(self.port) in range(1,65534):
                return True
            else:
                return False
        elif self.attr == 'uuid':
                if self.nodeUUID == '':
                    data = uuid.uuid4().hex[16:]
                    self.nodeUUID = data
                    return True
                elif len(self.nodeUUID) != 16:
                    return False
                else:
                    return True

    def connection_test(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.address, int(self.port)))
            except Exception:
                return False
            s.close()
            return True

    def write_config(self):
        config.add_section('HOST_INFO')
        config.set('DEFAULT','reportURL','http://adsb.feeyo.com/adsb/ReceiveCompressADSB.php')
        config.set('DEFAULT','uuid',self.nodeUUID)
        config.set('DEFAULT','version','0.1.0')
        config.set('HOST_INFO','address',self.address)
        config.set('HOST_INFO','port',self.port)
        with open(configLocation, 'w') as configfile:
            config.write(configfile)
            configfile.close()
        os.system('/bin/systemctl enable vffeeder')
        confirmInput = input('Would you like to enable auto-update for vffeeder? You will need to manually update it if auto-update is disabled. [Y/n]')[:1]
        if confirmInput == 'y' or confirmInput == '' or confirmInput == 'Y':
            updateCommand = '0 0 * * * /usr/local/bin/vffeeder update'
            with open('/var/spool/cron/crontabs/vffeeder', 'w') as cronjob:
                cronjob.write(updateCommand)
                cronjob.close()
        return

class Update:
    def check(self):
        config.read(configLocation)
        currentVersion = self.parse_version(config.get('DEFAULT','version'))
        getVersion = urllib.request.urlopen(url = 'https://raw.githubusercontent.com/Baka-D/vffeeder/master/vffeeder.ini')
        config.read_string(getVersion.read().decode())
        self.latestVersion = config.get('DEFAULT','version')
        if currentVersion < self.parse_version(self.latestVersion):
            self.upgrade()
        print('This is the latest version, no need to update.')
        exit()

    def parse_version(self, data):
        versionFull = data.split('.')
        version = ()
        for versionNumber in versionFull:
            version = version + (versionNumber,)
        return version

    def upgrade(self):
        scriptLocation = os.path.abspath(__file__)
        getLatest = urllib.request.urlopen(url = 'https://raw.githubusercontent.com/Baka-D/vffeeder/master/vffeeder.py')
        latestScript = getLatest.read().decode()
        config.read(configLocation)
        config.set('DEFAULT','version',self.latestVersion)
        with open(configLocation, 'w') as configfile:
            config.write(configfile)
            configfile.close()
        with open(scriptLocation, 'w') as scriptFile:
            scriptFile.write(latestScript)
            scriptFile.close()
        os.system('/bin/systemctl restart vffeeder')
        print('Update completed successfully!')
        exit()

def help():
    print('Usage:')
    print('    vffeeder - Start feeding to VariFlight\'s server')
    print('    vffeeder update - Check and update to the latest version of vffeeder')
    print('    vffeeder signup - Configure and setup vffeeder')
    exit()

def send_report(data):
    data = base64.b64encode(zlib.compress(data))
    try:
        urllib.request.urlopen(url = config.get('DEFAULT','reportURL'), data = urllib.parse.urlencode({'from': config.get('DEFAULT','uuid'), 'code': data}).encode('ascii'))
    except:
        print('Failed to contact with feed server.')

def get_report():
    config.read(configLocation)
    HOST = config.get('HOST_INFO','address')
    PORT = int(config.get('HOST_INFO','port'))

    while True:
        while True:
            try:
                s = socket.create_connection((HOST, PORT))
                break
            except:
                print('Failed to reach dump1090, please check your Internet connection, will try again in 10s.')
                sleep(10)
        data = s.recv(1024)
        send_report(data)

if len(sys.argv) == 1:
    get_report()
elif sys.argv[1] == 'signup':
    Register().check()
elif sys.argv[1] == 'update':
    Update().check()
elif sys.argv[1] == 'help':
    help()
else:
    print('Invalid argument.\n    use \'vffeeder help\' to get command list.')