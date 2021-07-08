#! /home/noc/bin/python

from netmiko import ConnectHandler, FileTransfer, file_transfer
import getpass
import datetime
from os import path

"""Test if list file exist"""
if path.exists("list.txt"):
    q = input('Do you want to use list.txt? y/n\n')
    if q is 'y' or 'Y':
        clist = True
        lfile = open("list.txt", 'r')
        lines = lfile.readlines()
    else:
        clist = False
else:
    clist = False
    ip = input("What is the ASA IP?\n")

count = 1

""""Grabbing Variables"""
username = 'automation'
password = getpass.getpass('Automation Password?\n')
sfile = input('What is the source file name?\n')

""""Check if ASAOS Image is good or not"""
if path.exists(sfile):
    pass
else:
    print("ASAOS Image supplied does not exist in supplied location\n Exiting...")
    exit()


def main(ip, user, psd, asaos):
    """Upgrade Script for ASA Devices"""
    start_time = datetime.datetime.now()

    asa_device = {
        'device_type': 'cisco_asa',
        'ip': ip,
        'username': user,
        'password': psd,
        'secret': psd,
        'port': 22
    }

    print("Attempting login to ASA")
    try:
        ssh_conn = ConnectHandler(**asa_device)
        print('Login Successful\n')
    except:
        print('Login Failed')
        exit()

    dest_file_system = 'disk0:'
    dest_file = asaos

    with FileTransfer(ssh_conn, source_file=asaos, dest_file=dest_file,
                      file_system=dest_file_system) as scp_transfer:

        if not scp_transfer.check_file_exists():
            if not scp_transfer.verify_space_available():
                raise ValueError("Insufficient space available on remote device")
            print("\nTransferring file\n")
            scp_transfer.transfer_file()
            print("Transfer Complete\n")
    print("\nChecking for current boot lines and removing.")
    testb = ssh_conn.send_command('show run boot')
    if testb != "":
        print('Current Boot Lines: \n' + testb)
        bootlist = []
        for bootl in testb.split('\n'):
            if bootl != "":
                bootlist.append(bootl)
        for bline in bootlist:
            ssh_conn.send_config_set('no ' + bline)
    print("\nSending current boot commands")
    full_file_name = "{}/{}".format(dest_file_system, dest_file)
    boot_cmd = 'boot system {}'.format(full_file_name)
    output = ssh_conn.send_config_set([boot_cmd])
    print(output)

    print("\nVerifying state")
    output = ssh_conn.send_command('show boot')
    output1 = ssh_conn.send_command('show version | i Appliance Software')
    output2 = ssh_conn.send_command('show version | i register')
    print(output)
    print("Current ASAOS Version:\n" + output1)
    print("Verify Config Registrar, should be 0x1:\n" + output2)

    print("\nWrite Config")
    output = ssh_conn.send_command_expect('write mem')
    #output += ssh_conn.send_command('reload')
    #output += ssh_conn.send_command('y')
    print(output)

    print("\n>>>> {}".format(datetime.datetime.now() - start_time))
    print()


if clist is True:
    print("Loading from list of IPs")
    for iline in lines:
        print(iline)
    for line in lines:
        print(str(count) + ": " + str(line))
        main(line, username, password, sfile)
        count += 1
else:
    print("Single run on IP")
    main(ip, username, password, sfile)

print("================")
print("===End Script===")
print("================")