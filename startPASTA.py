#!/usr/bin/python3
import os

#start marker first run
print('First run, wait to find GUI directory...')
found = False
for root, _, files in os.walk(os.path.expanduser('~')):
  for name in files:
    if name=='package.json':
      path = os.path.join(root, name)
      fContent = open(path,'r').read()
      if 'JS-React-Electron implementation of the PASTA database' in fContent:
        found = True
        print('First run, found directory')
        break
  if found:
    break
path = os.path.dirname(path)

thisFile = open(__file__,'r')
thisFileContent = thisFile.read().split('\n')
thisFile.close()
outFile  = ''
for line in thisFileContent:
  if '#start marker first run' in line and not 'if' in line:
    outFile += '"'+'"'+'"\n'
  outFile += line+'\n'
  if '#end marker first run'in line and not 'if' in line:
    outFile += '"'+'"'+'"\n'
    outFile += 'path = "'+path+'"\n'
thisFile = open(__file__,'w')
thisFile.write(outFile)
thisFile.close()
#end marker first run

#change into directory and start
os.chdir(path)
os.system('npm start')





