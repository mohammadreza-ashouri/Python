#!/usr/bin/python3
""" TEST ALL THE CODES: Python, ElectronDOM,...
might use lots of waiting time to ensure that things are finished
"""
import subprocess, os, time, re, sys, datetime
from pprint import pprint
import unittest
import shutil, json, psutil
import numpy as np


## TEST PYTHON CODE
def testPython():
  """
  Test Python code
  """
  print('==== PYTHON ====')
  os.chdir('Python')
  ### pylint
  success = True
  for fileName in ['backend.py', 'database.py', 'pastaCLI.py', 'pastaDB.py', 'miscTools.py', 'checkAllVersions.py']:
    result = subprocess.run(['pylint',fileName], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if 'rated at 10.00/10' not in result.stdout.decode('utf-8'):
      print(fileName+'|'+result.stdout.decode('utf-8').strip())
      success = False
  for fileName in os.listdir('extractors'):
    if not fileName.endswith('.py'): continue
    result = subprocess.run(['pylint','extractors/'+fileName], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if 'rated at 10.00/10' not in result.stdout.decode('utf-8'):
      print(fileName+'|'+result.stdout.decode('utf-8').strip())
      success = False
  if success:
    print('  success: pylint-success')
  else:
    print('  FAILED : pylint not 100%. run "pylint [file]"')
  ### git test
  result = subprocess.run(['git','status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  if len([1 for i in result.stdout.decode('utf-8').split('\n') if i.startswith('\tmodified:')])==0:
    print('  success: Git tree clean')
  else:
    print('  Warning : Submit to git')
    return
  # Git, expect clean git before testing
  ### TESTS
  for fileI in os.listdir('Tests'):
    if not fileI.startswith('test'): continue
    result = subprocess.run(['python3','-m','unittest','Tests'+os.sep+fileI], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    success = result.stdout.decode('utf-8').count  ('*** DONE WITH VERIFY ***')
    if success==1:
      print("  success: Python unit test: "+fileI)
    else:
      print("  FAILED: Python unit test: "+fileI)
      print("    run: 'python3 -m unittest Tests/"+fileI+"'")
  #### section = re.findall(r'Ran \d+ tests in [\d\.]+s\\n\\n..',str(result.stdout.decode('utf-8')))

  cmd = 'python3 Tests/testTutorial.py'.split(' ')
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  ## test read and write structure
  cmd = 'pastaDB.py -d pasta_tutorial print'.split(' ')
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  #### determine docID
  docID = None
  for line in result.stdout.decode('utf-8').split('\n'):
    if 'Intermetals at int' in line:
      docID = line.split()[-1]
  if docID is None:
    print('**ERROR** "Intermetals it int" not found as project')
    print(result.stdout.decode('utf-8'))
    return
  #### get current string
  cmd = ['pastaDB.py']+'hierarchy -d pasta_tutorial -i'.split(' ')+[docID]
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
  if lastLine=='SUCCESS':
    text = result.stdout.decode('utf-8').split('\n')[:-2]
    #### set string to old one
    cmd  = ['pastaDB.py','saveHierarchy','-d','pasta_tutorial','-i',docID,'-c','"'+'\\n'.join(text)+'"']
    # print('Command is: \n',' '.join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
    if lastLine=='SUCCESS':
      print('  success pastaDB.py:  setEditString')
    else:
      print('  FAILED pastaDB.py:  setEditString')
      print(result.stdout.decode('utf-8'))
  else:
    print('  FAILED pastaDB.py hierarchy: ')
    print(result.stdout.decode('utf-8'))

  ## Test all other pastaDB.py commands
  tests = ['test -d pasta_tutorial',
           'scanHierarchy -d pasta_tutorial -i '+docID,
           'print -d pasta_tutorial',
           'print -d pasta_tutorial -l project',
           'print -d pasta_tutorial -l measurement',
           'print -d pasta_tutorial -l sample',
           'print -d pasta_tutorial -l procedure',
           'extractorTest -d pasta_tutorial -p IntermetalsAtInterfaces/002_SEMImages/Zeiss.tif',
           'extractorTest -d pasta_tutorial -p IntermetalsAtInterfaces/002_SEMImages/Zeiss.tif -c measurement/tif/image/scale/adaptive']
  for test in tests:
    cmd = ['pastaDB.py']+test.split(' ')
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
    if lastLine=='SUCCESS':
      print('  success pastaDB.py: ',test)
    else:
      print('  FAILED pastaDB.py: ',test)
      print(result.stdout.decode('utf-8'))
  os.chdir('..')
  return


def compareDOM_ELECTRON():
  """
  COMPARE REACT-DOM AND REACT-ELECTRON
  """
  failure = False
  now = datetime.datetime.now().replace(microsecond=0)
  print('==== Compare ReactDOM and ReactElectron ====')
  print('  App.js and index.js should be different but changes should be propagated')
  result = subprocess.Popen(['diff','-q','ReactDOM/src','ReactElectron/app/renderer'], stdout=subprocess.PIPE)
  result.wait()
  result = result.stdout.read()
  result = result.decode('utf-8').split('\n')
  for line in result:
    if 'differ' in line and 'Files' in line:
      domFile = line.split()[1]
      electronFile = line.split()[3]
      if 'localInteraction.js' in domFile: continue
      domTime =      now-datetime.datetime.fromtimestamp(os.path.getmtime(domFile)).replace(microsecond=0)
      electronTime = now-datetime.datetime.fromtimestamp(os.path.getmtime(electronFile)).replace(microsecond=0)
      print("  Files are different\t\t\tTime since change\n   ",domFile,'\t\t',domTime,'\n   ',electronFile,'\t',electronTime)
      if not 'App.js' in domFile and not 'index.js' in domFile:
        failure=True
        if domTime<electronTime:
          print('    -> DOM is newer: copy file')
          shutil.copy(domFile,electronFile)
        else:
          print('    -> Electron is newer: copy file')
          shutil.copy(electronFile,domFile)
    if 'Only' in line:
      if 'App.test.js' in line: continue
      print("  File only in one directory",' '.join(line.split()[2:]))
  result = subprocess.Popen(['diff','-q','ReactDOM/src/components','ReactElectron/app/renderer/components'], stdout=subprocess.PIPE)
  result.wait()
  result = result.stdout.read()
  result = result.decode('utf-8').split('\n')
  for line in result:
    if 'differ' in line and 'Files' in line:
      domFile = line.split()[1]
      electronFile = line.split()[3]
      domTime =      now-datetime.datetime.fromtimestamp(os.path.getmtime(domFile)).replace(microsecond=0)
      electronTime = now-datetime.datetime.fromtimestamp(os.path.getmtime(electronFile)).replace(microsecond=0)
      print("  Files are different\t\t\tTime since change\n   ",domFile,'\t\t',domTime,'\n   ',electronFile,'\t',electronTime)
      failure=True
      if domTime<electronTime:
        print('    -> DOM is newer: copy file')
        shutil.copy(domFile,electronFile)
      else:
        print('    -> Electron is newer: copy file')
        shutil.copy(electronFile,domFile)
    if 'Only' in line:
      print("  File only in one directory",' '.join(line.split()[2:]))
      failure=True
  if failure:
    print('  FAILURE OF COMPARE')
  else:
    print('  success of compare')
  return



def testDOM():
  """
  TEST REACT-DOM CODE
  """
  print('==== ReactDOM ====')
  os.chdir('ReactDOM')
  ### js-lint
  success = True
  for root, _, files in os.walk("src"):
    for name in files:
      if not name.endswith('.js'):
        continue
      path = os.path.join(root, name)
      result = subprocess.run(['npx','eslint','--fix',path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
      if result.stdout.decode('utf-8').strip()!='':
        print(path+'|'+result.stdout.decode('utf-8').strip())
        success = False
  if success:
    print('  success: eslint-success')
  else:
    print('  FAILED : eslint not 100%. run "npx eslint [file]"')
  ### git test
  result = subprocess.check_output(['git','status'], stderr=subprocess.STDOUT)
  if len([1 for i in result.decode('utf-8').split('\n') if i.startswith('\tmodified:')])==0:
    print('  success: Git tree clean')
  else:
    print('  Warning : Submit to git')
    return  #skip other tests since they fail if linting fails.
  # Git, expect clean git before testing

  ### cypress, after linting
  text = None
  with open('src/localInteraction.js','r') as fIn:
    text = fIn.read()
  text = text.replace('const ELECTRON = false;','const ELECTRON = true;')
  with open('src/localInteraction.js','w') as fOut:
    fOut.write(text)
  print('  -- Start cypress test: Be patient!')
  server = subprocess.Popen(['npm','start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  result = subprocess.run(['npx','cypress','run','-q'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  result = result.stdout.decode('utf-8').split('\n')
  failures = [line for line in result if 'failures": [' in line]
  failures = ['[]' not in line for line in failures]
  if np.any(failures):
    print('  FAILED : cypress ')
    print('    Title of test: '+str(np.array([line for line in result if 'fullTitle"' in line][::2])[failures]))
    print('    File of failed test: '+str([line for line in result if '"relativeFile"' in line][::4]) )
    print('    Message of failure: '+str([line for line in result if '"message"' in line][::4]))
  else:
    print('  success: cypress')
  text = None
  with open('src/localInteraction.js','r') as fIn:
    text = fIn.read()
  text = text.replace('const ELECTRON = true;','const ELECTRON = false;')
  with open('src/localInteraction.js','w') as fOut:
    fOut.write(text)
  # find all children processes and terminate everything
  allPIDs = [server.pid]
  allPIDs += [i.pid for i in psutil.Process(allPIDs[0]).children(recursive=True)]
  for pid in allPIDs:
    psutil.Process(pid).terminate()
  print('  -- Server stopped')
  ## Done with all
  os.chdir('..')
  return


def testElectron():
  """
  TEST REACT-ELECTRON CODE
  """
  print('==== ReactElectron ====')
  os.chdir('ReactElectron')
  ### git test
  result = subprocess.check_output(['git','status'], stderr=subprocess.STDOUT)
  if len([1 for i in result.decode('utf-8').split('\n') if i.startswith('\tmodified:')])==0:
    print('  success: Git tree clean')
  else:
    print('  Warning: Submit to git')
  # success = True
  # for root, dirs, files in os.walk("app/renderer"):
  #   for name in files:
  #     if not name.endswith('.js'):
  #       continue
  #     path = os.path.join(root, name)
  #     print("check file:",path)
  #     result = subprocess.run(['npx','eslint','--fix',path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  #     if result.stdout.decode('utf-8').strip()!='':
  #       print(path+'|'+result.stdout.decode('utf-8').strip())
  #       success = False
  # if success:
  #   print('  success: eslint-success')
  # else:
  #   print('  FAILED : eslint not 100%. run "npx eslint [file]"')
  os.chdir('..')
  return


def testDocumentation():
  """
  TEST DOCUMENTATION
  """
  print('==== Documents ====')
  os.chdir('Documents')
  ### git test
  result = subprocess.check_output(['git','status'], stderr=subprocess.STDOUT)
  if len([1 for i in result.decode('utf-8').split('\n') if i.startswith('\tmodified:')])==0:
    print('  success: Git tree clean')
  else:
    print('  FAILED : Submit to git')
  return


def cleanAll():
  """
  Clean all versions
  """
  print('==== Clean all versions ====')
  for root, _, files in os.walk('.'):
    for name in files:
      if name.endswith('.orig'):
        print('  remove file:',os.path.join(root, name))
        os.remove( os.path.join(root, name) )
  return


if __name__=='__main__':
  if len(sys.argv)>1:
    if 'Python' in sys.argv[1]:
      testPython()
    elif sys.argv[1]=='compare':
      compareDOM_ELECTRON()
    elif 'DOM' in sys.argv[1]:
      testDOM()
    elif 'Electron' in sys.argv[1]:
      testElectron()
    elif sys.argv[1]=='Documentation':
      testDocumentation()
    elif sys.argv[1]=='cleanAll':
      cleanAll()
    else:
      print("Did not understand. Possible options are: Python, DOM, Electron, Documentation, compare")
  else:
    testPython()
    compareDOM_ELECTRON()
    testDOM()
    testElectron()
    testDocumentation()
    cleanAll()
    print('Only if all success: git push [everywhere]')
