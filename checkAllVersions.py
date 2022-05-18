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
  for fileName in ['backend.py', 'database.py', 'pastaELN.py', 'miscTools.py', 'checkAllVersions.py']:
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
    print('**FAILED : pylint not 100%. run "pylint [file]"')

  ### git test
  result = subprocess.run(['git','status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  if len([1 for i in result.stdout.decode('utf-8').split('\n') if (i.startswith('\tmodified:') and i!='\tmodified:   commonTools.py')])==0:
    print('  success: Git tree clean')
  else:
    print('**WARNING: Check code and submit to git')
    # os.chdir('..')
    # return
  # Git, expect clean git before testing
  #

  # run miscTools
  result = subprocess.run(['python3','./miscTools.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
  print(result.stdout.decode('utf-8').strip())

  ### TESTS  ###
  successAll = True
  for fileI in os.listdir('Tests'):
    if not fileI.startswith('test'): continue
    result = subprocess.run(['python3','-m','unittest','Tests'+os.sep+fileI], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    success = result.stdout.decode('utf-8').count  ('*** DONE WITH VERIFY ***')
    if success==1:
      print("  success: Python unit test "+fileI)
    else:
      successAll = False
      print("  FAILED: Python unit test "+fileI)
      print("    run: 'python3 Tests/"+fileI+"'")
  #### section = re.findall(r'Ran \d+ tests in [\d\.]+s\\n\\n..',str(result.stdout.decode('utf-8')))

  ### SUB-TESTS that depend on tutorial-complex
  cmd = 'python3 Tests/testTutorialComplex.py'.split(' ')
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  successAll = True
  for fileI in os.listdir('Tests'):
    if not fileI.startswith('subtest'): continue
    result = subprocess.run(['python3','-m','unittest','Tests'+os.sep+fileI], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    success = result.stdout.decode('utf-8').count  ('*** DONE WITH VERIFY ***')
    if success==1:
      print("  success: Python sub-unit test "+fileI)
    else:
      successAll = False
      print("**FAILED: Python sub-unit test "+fileI)
      print("    run: 'python3 Tests/"+fileI+"'")
  #### section = re.findall(r'Ran \d+ tests in [\d\.]+s\\n\\n..',str(result.stdout.decode('utf-8')))


  ## test read and write structure
  cmd = 'pastaELN.py -d pasta_tutorial print'.split(' ')
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  #### determine docID
  docID = None
  for line in result.stdout.decode('utf-8').split('\n'):
    if 'Intermet' in line:
      docID = line.split()[-1]
  if docID is None:
    successAll = False
    print('**ERROR** "Intermet" not found as project')
    print(result.stdout.decode('utf-8'))
    os.chdir('..')
    return
  #### get current string
  cmd = ['pastaELN.py']+'hierarchy -d pasta_tutorial -i'.split(' ')+[docID]
  result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
  if lastLine=='SUCCESS':
    text = result.stdout.decode('utf-8').split('\n')[:-2]
    #### set string to old one
    cmd  = ['pastaELN.py','saveHierarchy','-d','pasta_tutorial','-i',docID,'-c',"'"+'\\n'.join(text)+"'"]
    # print('Command is: \n',' '.join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
    if lastLine=='SUCCESS':
      print('  success pastaELN.py  setEditString2')
    else:
      successAll = False
      print('**FAILED pastaELN.py  setEditString2')
      print(result.stdout.decode('utf-8'))
  else:
    successAll = False
    print('**FAILED pastaELN.py hierarchy: ')
    print(result.stdout.decode('utf-8'))

  ## Blocking Test all other pastaELN.py commands
  tests = ['test -d pasta_tutorial',
           'scanHierarchy -d pasta_tutorial -i '+docID,
           'print -d pasta_tutorial',
           'print -d pasta_tutorial -l x0',
           'print -d pasta_tutorial -l measurement',
           'print -d pasta_tutorial -l sample',
           'print -d pasta_tutorial -l procedure']
  for test in tests:
    cmd = ['pastaELN.py']+test.split(' ')
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    lastLine = result.stdout.decode('utf-8').split('\n')[-2].strip()
    if lastLine=='SUCCESS':
      print('  success pastaELN.py ',test)
    else:
      successAll = False
      print('**FAILED pastaELN.py ',test)
      print(result.stdout.decode('utf-8'))
  ## NON-Blocking Test all other pastaELN.py commands
  tests = [
           'extractorTest -d pasta_tutorial -p IntermetalsAtInterfaces/002_SEMImages/Zeiss.tif',
           'extractorTest -d pasta_tutorial -p IntermetalsAtInterfaces/002_SEMImages/Zeiss.tif -c measurement/tif/image/scale/adaptive']
  for test in tests:
    cmd = ['pastaELN.py']+test.split(' ')
    _   = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  os.chdir('..')
  if successAll:
    print("ALL SUCCESS: GIT PUSH ")
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
      if 'localInteraction.js' in domFile:
        continue
      domTime =      now-datetime.datetime.fromtimestamp(os.path.getmtime(domFile)).replace(microsecond=0)
      electronTime = now-datetime.datetime.fromtimestamp(os.path.getmtime(electronFile)).replace(microsecond=0)
      print("  Files are different\t\t\tTime since change\n   ",domFile,'\t\t',domTime,'\n   ',electronFile,'\t',electronTime)
      if not 'App.js' in domFile and not 'index.js' in domFile:
        os.system('kdiff3 '+domFile+' '+electronFile)
        if not 'errorCodes.js' in domFile:
          failure=True
        if domTime<electronTime:
          print('    -> DOM is newer: copy file')
          shutil.copy(domFile,electronFile)
        else:
          print('    -> Electron is newer: copy file')
          shutil.copy(electronFile,domFile)
    if 'Only' in line:
      if 'App.test.js' in line:
        continue
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
      os.system('kdiff3 '+domFile+' '+electronFile)
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
    print('**FAILURE of compare')
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
    os.chdir('..')
    return  #skip other tests since they fail if linting fails.
  ### git test
  result = subprocess.check_output(['git','status'], stderr=subprocess.STDOUT)
  if len([1 for i in result.decode('utf-8').split('\n') if i.startswith('\tmodified:')])==0:
    print('  success: Git tree clean')
  else:
    print('**WARNING: Check code and submit to git')
    # os.chdir('..')
    # return
  # Git, expect clean git before testing (not easy since, linting/etc. can cause small changes)

  ### cypress, after linting
  text = None
  with open('src/localInteraction.js','r') as fIn:
    text = fIn.read()
  text = text.replace('const ELECTRON = false;','const ELECTRON = true;')
  with open('src/localInteraction.js','w') as fOut:
    fOut.write(text)
  print('  -- Start cypress test: Be patient!')
  server = subprocess.Popen(['npm','start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  time.sleep(60)
  result = subprocess.run(['npx','cypress','run','-q'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
  result = result.stdout.decode('utf-8').split('\n')
  failures = [line for line in result if 'failures": [' in line]
  failures = ['[]' not in line for line in failures]
  if np.any(failures):
    print('**FAILED : cypress failed test')
    print('    - '+'\n    - '.join(np.array([line[20:-3].strip() for line in result if 'fullTitle"' in line][::2])[failures]))
    # print('    Message of failure: '+str([line for line in result if '"message"' in line][::4]))
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
    print('**Warning: Submit to git')
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
  Clean all versions: currently not needed
  """
  # print('==== Clean all versions ====')
  # for root, _, files in os.walk('.'):
  #   for name in files:
  #     if name.endswith('.orig'):
  #       print('  remove file:',os.path.join(root, name))
  #       os.remove( os.path.join(root, name) )
  return


def gitStatus():
  """
  Go through all subfolders and do a git status
  """
  for i in ['Python','ReactDOM','ReactElectron','Documents']:
    print("\n\n------------------------------\nENTER DIRECTORY:",i)
    os.chdir(i)
    os.system('git status')
    os.chdir('..')
  return


def gitCommitPush(msg1, version=None, msg2=''):
  """
  Go through all subfolders and
    - do a git commit with message msg
    - tag it with a version number
    - git push

  Args:
    msg1 (string): message for git commit
    version (string): new version number; if not given, increment the last digit by one
    msg2 (string): message to the tag
  """
  for i in ['Python','ReactDOM','ReactElectron','Documents']:
    print("\n\n------------------------------\nENTER DIRECTORY:",i)
    os.chdir(i)
    if version is None and i=='Python':
      result = subprocess.run(['git','tag'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
      version= result.stdout.decode('utf-8').strip()
      version= version.split('\n')[-1]
      verList= [int(i) for i in version[1:].split('.')]
      verList[-1]+= 1
      version= 'v'+'.'.join([str(i) for i in verList])
    if i=='ReactElectron':
      ### package.json ###
      with open('package.json') as fIn:
        packageOld = fIn.readlines()
      packageNew = []
      for line in packageOld:
        line = line[:-1]
        if '"version":' in line:
          line = '  "version": "'+version[1:]+'",'
        packageNew.append(line)
      with open('package.json','w') as fOut:
        fOut.write('\n'.join(packageNew)+'\n')
      ### version in configuration.js ###
      with open('app/renderer/components/ConfigPage.js') as fIn:
        fileOld = fIn.readlines()
      fileNew = []
      for line in fileOld:
        line = line[:-1]
        if '<p style={flowText}>Version number:' in line:
          line = '          <p style={flowText}>Version number: '+version[1:]+'</p>'
        fileNew.append(line)
      with open('app/renderer/components/ConfigPage.js','w') as fOut:
        fOut.write('\n'.join(fileNew)+'\n')
    os.system('git commit -a -m "'+msg1+'"')
    os.system('git tag -a '+version+' -m "'+msg2+'"')
    os.system('git push')
    os.system('git push origin '+version)
    os.chdir('..')
  return

###################################################################
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
    elif sys.argv[1]=='gitStatus':
      gitStatus()
    elif sys.argv[1]=='gitCommitPush':
      message = sys.argv[2] if len(sys.argv)>2 else ''
      tagString     = sys.argv[3] if len(sys.argv)>3 else ''
      versionString = sys.argv[4] if len(sys.argv)>4 else None
      gitCommitPush(message, versionString, tagString)
    else:
      print('Did not understand. Possible options are: Python, DOM, Electron, Documentation, compare, gitStatus, gitCommitPush')
      print('  gitCommitPush: commit_message tag_messag tag_version')
  else:
    testPython()
    compareDOM_ELECTRON()
    testDOM()
    testElectron()
    testDocumentation()
    cleanAll()
    print('Only if all success: git push [everywhere]')
