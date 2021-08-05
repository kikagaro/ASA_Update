#! /home/noc/bin/python
import scp
from netmiko import ConnectHandler, FileTransfer
import getpass
import datetime
import re
from os import path

'''Test if list file exist'''
if path.exists("list.txt"):
    q = input('list.txt detected.\nDo you want to use list.txt? [Y/n]\n')
    if q.lower() == 'y':
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
if rcheck.lower() == "y":
    rommonfile = input("What is the ROMMON file name?\n")
    if path.exists(rommonfile):
        rommon = True
        pass
    else:
        print("ROMMON Image supplied does not exist in supplied location\n Exiting...")
        exit()
else:
    rommon = False
    rommonfile = None


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
    asaImages = {
        '5506': {
            'os': 'asa9-14-2-15-lfbff-k8.SPA',
            'rommon': 'asa5500-firmware-1118.SPA'
        },
        '5512': {
            'os': 'asa9-12-4-26-smp-k8.bin'
        },
        '5515': {
            'os': 'asa9-12-4-26-smp-k8.bin'
        },
        '5525': {
            'os': 'asa9-12-4-26-smp-k8.bin'
        },
        '5545': {
            'os': 'asa9-12-4-26-smp-k8.bin'
        }
    }

    print("Attempting login to ASA")
    try:
        ssh_conn = ConnectHandler(**asa_device)
        print('Login Successful\n')
    except:
        print('Login Failed')
        exit()

    dest_file_system = 'disk0:'

    def hwModel():
        output = ssh_conn.send_command('show run | i Hardware')
        print(output)
        for x in output.strip('\n'):
            print(x)
            type(x)
            hwversion = re.search('ASA\d+', x)
            print(hwversion)
            type(hwversion)
            hwnum = hwversion[0].strip('ASA')
        print(hwnum)
        return hwnum

    """Test"""
    hwModel()
    exit()

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

    """Function to check for errors that could occur during upload
    and reboot process."""
    def errorCheck():
        """Config lines to check for"""
        cryptoMap = [
            '^crypto map outside_map \d+? set pfs group1$',
            '^crypto map outside_map \d+? set pfs$'
        ]
        cryptoIkev = [
            '^ group 1$'
        ]
        HWVersion = [
            'V01',
            'V02',
            'V03'
        ]
        failed = []
        check = True
        hwCheck = True
        donotpassgo = False
        """check for Crypto Map changes/adjustments"""
        print('Checking Crypto configurations for possible problems.')
        print('Checking Crypto map configs...')
        output = ssh_conn.send_command('sh run crypto map')
        for x in output.split('\n'):
            for c in cryptoMap:
                if re.match(c, x.strip()):
                    check = False
                    failed.append(x)
        if not check:
            print('Invalid Crypyo Map Lines:')
            for v in failed:
                print(v)
                failed = []
            check = True
        else:
            print("Pass")
        print('Checking Crypto IKEV1 configs...')
        output = ssh_conn.send_command('sh run crypto ikev1')
        for x in output.split('\n'):
            for c in cryptoIkev:
                if re.match(c, x):
                    check = False
                    failed.append(x)
        if not check:
            print('Found Ikev1 DH Group1 in config.')
            check = True
        else:
            print('Pass')
        print('Checking Crypto IKEV2 configs...')
        output = ssh_conn.send_command('sh run crypto ikev2')
        for x in output.split('\n'):
            for c in cryptoIkev:
                if re.match(c, x):
                    check = False
                    failed.append(x)
        if not check:
            print('Found Ikev2 DH Group1 in config.')
            check = True
        else:
            print('Pass')
        """Adding Hardware Version check for 5506"""
        print("Checking for 5506 hardware revision...")
        output = ssh_conn.send_command('sh inv')
        for x in output.split('\n'):
            for c in HWVersion:
                if re.match('^PID: ASA5506 ', x.strip()) and re.findall(c, x.strip()):
                    hwCheck = False
        if not hwCheck:
            print('5506 Model is V01/02/03. Replace instead of upgrade.')
            hwCheck = True
            donotpassgo = True

        else:
            print('Pass')
        return donotpassgo

    """Running Error Check"""
    if not errorCheck():
        '''Transferring ASAOS and ROMMON Image'''
        transfer(asaos, asaos, dest_file_system)
        if rstate:
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
        full_file_name = "{}/{}".format(dest_file_system, asaos)
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
        print(output)
        """Disabling This for now as Reloads are to be scheduled"""
        '''
        reload = input('Do you wish to apply the ROMMON upgrade or reboot now? [Y/n]\n')
        if reload is 'Y' or 'y':
            if rstate is True:
                print('Applying ROMMON upgrade')
                output = ssh_conn.send_command('upgrade rommon ' + dest_file_system + '/' + dest_rfile)
                output += ssh_conn.send_command('y')
                print(output)
            else:
                output = ssh_conn.send_command('reload')
                output += ssh_conn.send_command('y')
                print(output)
        '''
        print("\n>>>> {}".format(datetime.datetime.now() - start_time))
        print()


if clist is True:
    print("Loading from list of IPs")
    for iline in lines:
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
