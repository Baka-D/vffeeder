#!/bin/bash
#
#This script is writen for VariFlight's ADS-B Feed Program.
#You need to have an existing dump1090 installation to paticipent in this project.
#You could learn more at https://flightadsb.variflight.com/
#
#System requirements: Centos 7+, Debian 8+, Ubuntu 14+

[[ $EUID -ne 0 ]] && echo 'Please run this script as root!' && exit 1

disable_selinux(){
    if [ -s /etc/selinux/config ] && grep 'SELINUX=enforcing' /etc/selinux/config; then
        sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
        setenforce 0
    fi
}

detect_system(){
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ $ID_LIKE == "debian" ]] || [[ $ID == "debian" ]]; then
            packageManager='apt'
        elif [[ $ID_LIKE == "rhel fedora" ]]; then
            packageManager='yum'
        else
            echo 'Unsupported system.'
            exit 1
        fi
    fi
}

pre_install(){
    detect_system
    echo -n 'Please enter the IP address for your existing dump1090 instance. '
    read -p 'IP address: ' instanceAddress
    echo -n 'Please enter your feeder UUID if you already have one, otherwise leave it blank. '
    read -p 'UUID: ' instanceUuid
    read -n 1 -p 'Do you want to continue? [Y/n]' confirmInput
    if [[ $confirmInput == 'y' ]] || [[ $confirmInput == 'Y' ]] || [[ $confirmInput == '' ]]; then
        if [[ $packageManager == 'apt' ]]; then
            apt update -y
        fi
        $packageManager -y install python3 curl systemd
        install_feeder
        if [[ $instanceUuid == '' ]]; then
            generate_uuid
        fi
        write_config
        install_service
        echo 'Vffeeder has been installed successfully!'
        echo 'Your UUID is' "$instanceUuid" ' Please register it at https://flightadsb.variflight.com/share-data/script'
    else
        echo 'Process aborted.'
        exit 1
    fi
}

generate_uuid(){
    beforeParse=$(cat /proc/sys/kernel/random/uuid)
    parsedUuid=${beforeParse//-/}
    instanceUuid=${parsedUuid:0:16}
}

install_feeder(){
    if [[ -f vffeeder.py ]]; then
        cp vffeeder.py /usr/local/bin/vffeeder
    else
        curl -s -o /usr/local/bin/vffeeder https://raw.githubusercontent.con/Baka-D/vffeeder/master/vffeeder.py
    fi
    chmod +x /usr/local/bin/vffeeder
}

write_config(){
    echo '[DEFAULT]' > /etc/vffeeder.ini
    echo 'uuid =' "$instanceUuid" >> /etc/vffeeder.ini
    echo 'reporturl = http://adsb.feeyo.com/adsb/ReceiveCompressADSB.php' >> /etc/vffeeder.ini
    echo '' >> /etc/vffeeder.ini
    echo '[HOST_INFO]' >> /etc/vffeeder.ini
    echo 'address =' "$instanceAddress" >> /etc/vffeeder.ini
    echo 'port = 30003' >> /etc/vffeeder.ini
}

install_service(){
    useradd vffeeder -M -s /usr/sbin/nologin
    touch /var/log/vffeeder.log
    chown vffeeder /var/log/vffeeder.log
    if [[ -f vffeeder.service ]]; then
        cp vffeeder.service /etc/systemd/system/vffeeder.service
    else
        curl -s -o /etc/systemd/system/vffeeder.service https://raw.githubusercontent.con/Baka-D/vffeeder/master/vffeeder.service
    fi
    chmod +x /etc/systemd/system/vffeeder.service
    /bin/systemctl enable vffeeder
    /bin/systemctl start vffeeder
}

pre_install