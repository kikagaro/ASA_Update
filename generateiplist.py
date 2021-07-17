#! /usr/bin/python

def generateips():
    from rancid.models import Device
    from os import path

    names = '/home/noc/philw/ASA_Update/names.txt'
    try:
        if path.exists(names):
            print('Names List exist.')
        else:
            print('Names List does not exist. please create the following file '
                  'with the list of firewall hostnames:\n' + names)
            exit()
    except:
        pass
        exit()

    with open(names, 'r') as r:
        list = [line.strip() for line in r]

    print('List of names to lookup: \n' + str(list))

    listfile = "/home/noc/philw/ASA_Update/list.txt"
    i = 1
    iplist = []

    for name in list:
        devices = Device.objects.filter(devicetype__name='asa', rancid=True, name__icontains=name).order_by('-priority', 'name')
        for device in devices:
            ip = device.ip.__str__()
            iplist.append(ip)
            print(i, device.name, ip + '\n')
            i += 1

    with open(listfile, 'w') as lf:
        for ipl in iplist:
            lf.write('%s\n' % ipl)

    print('List of IPs generated for devices:\n' + names)


print('Run this on noc as root user')
print('ds')
print('from philw.ASA_Update.generateiplist import generateips')
print('generateips()')
