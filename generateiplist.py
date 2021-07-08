#! /usr/bin/python

def generateips():
    from rancid.models import Device

    names = '/home/noc/philw/ASA_Update/names.txt'

    with open(names, 'r') as r:
        list = [line.strip() for line in r]

    print(list)

    listfile = "/home/noc/philw/ASA_Update/list.txt"
    i = 1
    iplist = []

    for name in list:
        devices = Device.objects.filter(devicetype__name='asa', rancid=True, name__icontains=name).order_by('-priority', 'name')
        for device in devices:
            ip = device.ip.__str__()
            iplist.append(ip)
            print(i, device.name, ip)
            i += 1

    print(iplist)

    with open(listfile, 'w') as lf:
        for ipl in iplist:
            lf.write('%s\n' % ipl)


print('Run this on noc as root user')
print('ds')
print('from philw.ASA_Update import generateiplist')
print('generateips()')
