import subprocess as sub
import functions  # noqa
from decorator import ping_functions, of_functions
from time import sleep


# Run in s1 of Mininet + Ryu
first = True
do_openflow = True
p = sub.Popen(('sudo', 'tcpdump', '-l', '-i', 'any'), stdout=sub.PIPE)
for row in iter(p.stdout.readline, b''):
    if 'ICMP' in row and 'request' in row:
        for function in ping_functions:
            function()
    if 'PACKET_IN' in row:
        if first:
            do_openflow = not do_openflow
            first = not first
        else:
            first = not first

    if do_openflow:
        for function in of_functions:
            function()
        sleep(1)
