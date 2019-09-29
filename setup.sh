#!/bin/bash
#
#This script is writen for Variflight's ADS-B Feed Program.
#You need to have an existing antenna to paticipent in this program.
#You could learn more at https://flightadsb.variflight.com/
#
#System requirements: Centos 7+, Debian 7+, Ubuntu 15+

[[ $EUID -ne 0 ]] && echo 'Please run this script as root!' && exit 1

disable_selinux(){
    if [ -s /etc/selinux/config ] && grep 'SELINUX=enforcing' /etc/selinux/config; then
        sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
        setenforce 0
    fi
}

detect_system(){
    if source /etc/os-release; then
        if [[ $ID_LIKE == 'debian' ]]; then
            packageManager='apt'
        elif [[ $ID_LIKE == 'rhel fedora' ]]; then
            packageManager='yum'
        else
            echo 'Unsupported system.'
            exit 1
        fi
    elif grep -Eiq 'red hat' /proc/version; then
        packageManager='yum'
    else
        echo 'Unsupported system.'
        exit 1
    fi
    if [[ $packageManager == 'yum' ]]; then
        RHELVER=$(rpm --eval %rhel)
        if [[ $RHELVER -ne 7 ]]; then
        	echo 'Unsupported RHEL version.'
         	exit 1
        fi
    fi
}

checkPython=0

check_python(){
    if which python3; then
        if which python3 != '/usr/bin/python3'; then
            ln -s $('which python3') /usr/bin/python3
        fi
        install_feeder
    elif [[ $checkPython -eq 0 ]]; then
        install_python3
    else
        compile_python3
    fi
}

install_python3(){
    detect_system
    read -n 1 -p 'Python 3 installetion not found, need to install Python 3 now. Do you want to continue? [Y/n]' confirmInput
    if [[ $confirmInput == 'y' ]] || [[ $confirmInput == 'Y' ]] || [[ $confirmInput == '' ]]; then
        if [[ $packageManager == 'apt' ]]; then
            apt update && apt install python3 curl systemd -y
        else
            yum -y install python3 curl systemd
        fi
        if [ $? -eq 0 ]; then
            checkPython=1
            check_python
        else
            compile_python3
        fi
    else
        echo 'Process aborted.'
        exit 1
    fi
}

compile_python3(){
    echo 'Failed to install Python 3 from your package manager, would you like to compile it from the source code? (This process may take a long time) [Y/n]' //TODO
}

install_feeder(){
    if ! curl -o /usr/local/bin/vffeeder https://raw.githubusercontent.com/Baka-D/vffeeder/master/vffeeder.py; then
        echo 'Failed to download feeder script'
        exit 1
    fi
    if ! curl -o /etc/systemd/system/vffeeder.service https://raw.githubusercontent.com/Baka-D/vffeeder/master/vffeeder.service; then
        echo 'Failed to download feeder service script'
        exit 1
    fi
    chmod +x /usr/local/bin/vffeeder
    useradd vffeeder -s /sbin/nologin -d /var/lib/vffeeder -m
}

main(){
    disable_selinux
    check_python
}

main