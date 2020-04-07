#!/usr/bin/python3
""" TEST ALL THE CODES: Python, ElectronDOM,...
lots of waiting time to ensure that things are finished
"""
import subprocess, os, time


## TEST PYTHON CODE
os.chdir('Python')
result = subprocess.run(['./verify.py'], stdout=subprocess.PIPE)
time.sleep(30)
output = result.stdout.decode('utf-8').split('\n')
logFile= open('jams.log','r').read().split('\n')
if output[-2]=='Replication test' and logFile[-2]=='END JAMS':  #last item is always empty: new line
  print("Python success")
else:
  print("Python failure")
  print(output)
result = subprocess.run(['git','status'], stdout=subprocess.PIPE)
time.sleep(3)
output = result.stdout.decode('utf-8').split('\n')
if output[-2]=='nothing to commit, working tree clean':
  print("  Git tree is clean")
else:
  print(output)
os.chdir('..')