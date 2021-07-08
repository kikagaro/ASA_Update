#! /home/noc/bin/python
import scp
from netmiko import ConnectHandler, FileTransfer
import getpass
import datetime
from os import path

'''Test if list file exist'''
if path.exists("list.txt"):
    q = input('list.txt detected.\nDo you want to use list.txt? y/n\n')
    if q is 'y' or 'Y':
        clist = True
        lfile = open("list.txt", 'r')
        lines = lfile.readlines()
    else:
        clist = False
        ip = input("What is the ASA IP?\n")
else:
    clist = False
    ip = input("What is the ASA IP?\n")

count = 1

""""Grabbing Variables"""
username = 'automation'
password = getpass.getpass('Automation Password?\n')
sfile = input('What is the ASAOS source file name?\n')
rcheck = input('Do you want to update the ROMMON image? [Y/n]\n')

'''Check if ASAOS Image is good or not'''
if path.exists(sfile):
    pass
else:
    print("ASAOS Image supplied does not exist in supplied location\n Exiting...")
    exit()
'''Check if ROMMON Image is good or not'''
if rcheck is "Y" or "y":
    rommonfile = input("What is the ROMMON file name?")
    if path.exists(rommonfile):
        rommon = True
        pass
    else:
        print("ROMMON Image supplied does not exist in supplied location\n Exiting...")
        exit()
else:
    rommon = False


def main(ip, user, psd, asaos, rstate=False, rfile=None):
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

    def transfer(source, destination, filesystem):
        with FileTransfer(ssh_conn, source_file=source, dest_file=destination,
                          file_system=filesystem) as scp_transfer:

            if not scp_transfer.check_file_exists():
                if not scp_transfer.verify_space_available():
                    raise ValueError("Insufficient space available on remote device")
                print("\nTransferring file:\n" + str(source))
                try:
                    scp_transfer.transfer_file()
                except scp.SCPException:
                    pass
                print("\nTransfer Complete\n")

    '''Transfering ASAOS and ROMMON Image'''
    transfer(asaos, asaos, dest_file_system)
    if rstate is True:
        transfer(rfile, rfile, dest_file_system)
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
    full_file_name = "{}/{}".format(dest_file_system, dest_os_file)
    boot_cmd = 'boot system {}'.format(full_file_name)
    output = ssh_conn.send_config_set([boot_cmd])
    print(output)
    '''Disabling ROMMON upgrade for now as it requires a reload while applying.'''
    """
    if rstate is True:
        print('Applying ROMMON upgrade')
        output = ssh_conn.send_command('upgrade rommon ' + dest_file_system + '/' + dest_rfile)
        output += ssh_conn.send_command('y')
        print(output)
    """
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
    for iline in lines.strip():
        print(iline)
    for ip in lines:
        print(str(count) + ": " + str(ip))
        main(ip, username, password, sfile, rommon, rommonfile)
        count += 1
else:
    print("Single run on IP")
    main(ip, username, password, sfile, rommon, rommonfile)

print("================")
print("===End Script===")
print("================")
