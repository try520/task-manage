#!/usr/bin/python3
import time
import sys


if(len(sys.argv) > 1):
    args = sys.argv[1]
else:
    args = 'hello'

for i in range(1, len(sys.argv)):
    print("参数", i, sys.argv[i])

while True:
    print(args)
    time.sleep(1)
