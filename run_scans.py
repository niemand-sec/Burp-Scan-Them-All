
from subprocess import Popen, PIPE, STDOUT,check_call,call
import os
import socket

source = 'pending_hosts.txt'
burp = "burpsuite_pro_v1.7.27.jar"
slack_token = "<yourstokenhere>"
cache_fix = True
slack_username = "niemand"
slack_channel = "burpreports"

def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0

def delete_host():
    with open(source, "r+") as f:
        data = f.readlines()
        scheme, domain, port, folder = data[0].split(",")
        print "[+] Deleting host {}://{}:{} from pending hosts".format(scheme, domain, port)
        f.seek(0)
        f.writelines(data[1:])
        f.truncate()
        f.close()

while True:  ##I know, I know it's a while true
    with open(source, 'r+') as f:
        lines = f.readlines()
        port, domain, scheme, folder = lines[0].strip().split(",")
        print "[+] Reading line from pending hosts..."
        print "[+] Starting script for {0}://{1}:{2}".format(scheme, domain, port)
        f.close()

        if cache_fix:
            print "[+] Clearing cache"
            Popen('sudo sysctl -w vm.drop_caches=3',shell=True, stderr=STDOUT)

        html = "IntegrisSecurity_Carbonator_{0}_{1}_{2}.html".format(scheme,domain,port)
        output_folder = "outputs_burp"


        if hostname_resolves(domain):
            print "[+] Host found in IP: %s" %socket.gethostbyname(domain)
            b = check_call(
                ['curl', '-F', 'text="Starting script for {0}://{1}:{2} @{3}"'.format(scheme, domain, port,slack_username), '-F',
                 'channel=#{}'.format(slack_channel), '-F', 'token={}'.format(slack_token),
                 'https://slack.com/api/chat.postMessage'])
        else:
            print "[!] Skipping host, couldn't resolve DNS"
            b = check_call(
                ['curl', '-F', 'text="Skipted for {0}://{1}:{2} @{3}"'.format(scheme, domain, port, slack_username), '-F',
                 'channel=#{}'.format(slack_channel), '-F', 'token={}'.format(slack_token),
                 'https://slack.com/api/chat.postMessage'])
            delete_host()
            continue

        try:
            Popen('mkdir -p {}/{}/'.format(output_folder,folder), shell=True, stderr=STDOUT)
        except:
            "[!] Folder already exists"

        p = call('java -jar -Djava.awt.headless=true {0} --config-file=config/project-config.json \
              --user-config-file=config/user-config.json \
              --project-file="{1}/{2}/{3}_{4}" --unpause-spider-and-scanner \
              {5} {3} {4}'.format(burp,output_folder,folder,domain,port,scheme),shell=True, stderr=STDOUT)


        check_call(['curl', '-F', 'file=@{}'.format(html),'-F','initial_comment="Report {}://{}:{} @{}"'.format(scheme, domain, port, slack_username),
                    '-F', 'channels=#{}'.format(slack_channel), '-F', 'token={}'.format(slack_token),
                    'https://slack.com/api/files.upload'])
        Popen('mv {} {}/{}/'.format(html, output_folder, folder), shell=True, stderr=STDOUT)


    with open(source, "r+") as f:
        data = f.readlines()
        print data
        port, domain, scheme, folder = lines[0].strip().split(",")
        print "[+] Deleting host {}://{}:{} from pending hosts".format(scheme, domain, port)
        f.seek(0)
        f.writelines(data[1:])
        f.truncate()
        f.close()
