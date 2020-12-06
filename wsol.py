#!/usr/bin/env python
# coding: utf-8

import sys
import ConfigParser
import argparse
import subprocess
import Tkinter as Tk
import paramiko
import wol

HOST = ''
MACADDR = ''
USER = ''

STATUS_COLOR = {
    '-':    'black',
    'UP':   'forest green',
    'DOWN': 'blue',
}

class Frame_wsol(Tk.Frame):
    def __init__(self, args, master=None):
        Tk.Frame.__init__(self, master)
        self.args = args
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=48)

        self.button_on = Tk.Button(self, text='ON', command=self.Wakeup)
        self.button_on.grid(row=0, column=0, sticky="news")

        self.button_off = Tk.Button(self, text='OFF', command=self.Shutdown)
        self.button_off.grid(row=1, column=0, sticky="news")

        self.label_status = Tk.Label(self, text='-', width=16, height=3,
                                     fg='white', bg='black')
        self.label_status.grid(row=0, column=1, rowspan=2, sticky="news")

        self.after(100, self.update)

    def update(self):
        status = ping(self.args.host)
        if status != '':
            self.label_status.configure(text=status)
            if status in STATUS_COLOR:
                self.label_status.configure(bg=STATUS_COLOR[status])
        self.after(1000, self.update)

    def Wakeup(self):
        wol.sendmagickpacket([self.args.macaddr])

    def Shutdown(self):
        shutdown(self.args.host, self.args.user, self.args.password)

def ping(ipaddr):
    """ipaddr に ping を打つ。結果に応じて文字列を返す

    'UP':   応答があった
    'DOWN': 応答がなかった
    '':     応答待ち
    """
    if not hasattr(ping, 'proc') or ping.proc is None:
        if sys.platform == 'win32':
            args = 'ping -n 1 -w 1000 %s' % (ipaddr,)
            cflag = 0x08000000
        else:
            args = ['ping', '-c 1', '-t 1', ipaddr]
            cflag = 0
        ping.proc = subprocess.Popen(args, creationflags=cflag,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        status = ''
    else:
        retcode = ping.proc.poll()
        if retcode is None:
            status = ''
        else:
            if sys.platform == 'win32':
                ping_output = ping.proc.communicate()[0]
                if ping_output.find('unreachable') >= 0 or ping_output.find(u'到達できません'.encode('cp932')) >= 0:
                    status = 'DOWN'
                elif ping_output.find('Received = 0') >= 0 or ping_output.find(u'受信 = 0'.encode('cp932')) >= 0:
                    status = 'DOWN'
                else:
                    status = 'UP'
            else:
                if retcode == 0:
                    status = 'UP'
                else:
                    status = 'DOWN'
            ping.proc = None

    return status

def shutdown(host, user, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    stdin, stdout, stderr = ssh.exec_command("sudo -S -p '' shutdown -h now")
    stdin.write(password + '\n')
    stdin.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wakeup/Shutdown the server.',
                                     add_help=False)
    parser.add_argument('-h', '--host', default=HOST)
    parser.add_argument('-m', '--macaddr', default=MACADDR)
    parser.add_argument('-u', '--user', default=USER)
    parser.add_argument('-p', '--password', default='')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w', '--wakeup', action='store_true', default=False)
    group.add_argument('-s', '--shutdown', action='store_true', default=False)
    group.add_argument('-g', '--gui', action='store_true', default=False)
    parser.add_argument('--help')

    args = parser.parse_args()
    if args.wakeup:
        wol.sendmagickpacket([args.macaddr])
    elif args.shutdown:
        shutdown(args.host, args.user, args.password)
    elif args.gui:
        f = Frame_wsol(args)
        #f.winfo_toplevel().wm_overrideredirect(1)
        f.pack(fill="both", expand="yes")
        f.mainloop()


