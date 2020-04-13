#!/usr/bin/python3
import os, shutil, traceback, sys
from agileScience import AgileScience
import asTools

### initialization
sys.path.append('/home/sbrinckm/FZJ/Code/Nanotribology')  #allow debugging in vscode which strips the python-path
databaseName = 'temporary_test'
dirName      = os.path.expanduser('~')+"/"+databaseName
os.makedirs(dirName, exist_ok=True)
be = AgileScience(databaseName)
be.exit(deleteDB=True)
be = AgileScience(databaseName)

try:
  ### create some test projects
  print("*** TEST PROJECTS ***")
  be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
  be.addData('project', {'name': 'Test project2', 'objective': 'Test objective2', 'status': 'passive', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
  be.addData('project', {'name': 'Test project3', 'objective': 'Test objective3', 'status': 'paused', 'comment': '#tag1 :field2:max: A random text'})
  print(be.output('Projects'))

  ### create some test steps and tasks
  print("*** TEST PROJECT HIERARCHY ***")
  doc = be.db.getView('viewProjects/viewProjects')
  projID  = [i['id'] for i in doc][0]
  be.changeHierarchy(projID)
  projDirName = be.basePath+be.cwd
  be.addData('step',    {'comment': 'More random text', 'name': 'Test step one'})
  be.addData('step',    {'comment': 'Much more random text', 'name': 'Test step two'})
  tempID = be.currentID
  be.addData('step',    {'comment': 'Even more random text', 'name': 'Test step three'})
  be.changeHierarchy(tempID)
  be.addData('task',    {'name': 'Test task une', 'comment': 'A random comment', 'procedure': 'Secret potion for Asterix'})
  be.addData('task',    {'name': 'Test task duo', 'comment': 'A comment', 'procedure': 'Secret potion for Obelix'})
  be.changeHierarchy(be.currentID)
  stepDirName = be.basePath+be.cwd
  be.addData('measurement', {'name': 'fallInPot.txt', 'comment': 'great fall'})
  be.addData('measurement', {'name': "https://pbs.twimg.com/profile_images/3044802226/08c344aa3afc2f724d1232fe0f040e07.jpeg", 'comment': 'years later'})
  be.changeHierarchy(None)
  be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})
  be.changeHierarchy(None)
  print(be.outputHierarchy())

  ### edit project
  print("*** TEST EDIT PROJECT ***")
  be.addData('-edit-', {'comment': '#tag1 A random text plus edition\n'})

  ### test procedures
  print("*** TEST PROCEDURES ***")
  be.addData('procedure', {'name': 'Test procedure 1', 'content': '1. grind, 2. polish, 3. microscope', 'comment': ''})
  be.addData('procedure', {'name': 'Test procedure 2', 'content': '1. grind, 2. microscope', 'comment': ''})
  be.addData('procedure', {'name': 'Test procedure 3', 'content': '1. polish, 2. microscope', 'comment': ''})
  be.changeHierarchy(None)
  be.addData('procedure', {'name': 'Test procedure without project', 'content': 'Secret potion for Asterix', 'comment': ''})
  print(be.output('Procedures'))

  ### test samples
  print("*** TEST SAMPLES ***")
  be.changeHierarchy(projID)
  be.addData('sample',    {'name': 'Big copper block', 'chemistry': 'Cu99.999', 'qr_code': '13214124 12341234', 'comment': '#save'})
  be.addData('sample',    {'name': 'Small copper block', 'chemistry': 'Cu99.99999', 'qr_code': '13214124111', 'comment': ''})
  be.addData('sample',    {'name': 'Big iron ore', 'chemistry': 'Fe', 'qr_code': '1321412411', 'comment': ''})
  be.addData('sample',    {'name': 'Ahoj-Brause Pulver', 'chemistry': '???', 'qr_code': '', 'comment': ''})
  be.addData('sample',    {'name': 'Gummibären', 'chemistry': '???', 'qr_code': '', 'comment': '6 pieces'})
  be.addData('sample',    {'name': 'Lutscher', 'chemistry': '???', 'qr_code': '', 'comment': ''})
  be.addData('sample',    {'name': 'Taschentücher', 'chemistry': '???', 'qr_code': '', 'comment': ''})
  print(be.output('Samples'))
  print(be.outputQR())

  ### test measurements
  print("*** TEST MEASUREMENTS AND SCANNING ***")
  be.addData('measurement', {'name': 'filename.txt', 'comment': '#random #5 great stuff'})
  be.addData('measurement', {'name': 'filename.jpg', 'comment': '#3 #other medium stuff'})
  shutil.copy(be.softwarePath+'/ExampleMeasurements/Zeiss.tif', projDirName)
  shutil.copy(be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', projDirName)
  shutil.copy(be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', stepDirName)
  be.scanTree(produceData=False, compareData=False, compareDoc=False)
  #use shutil to 1move data, 2copy data, 3rename file, 4rename folder
  be.scanTree(produceData=True, compareData=False, compareDoc=False)
  be.scanTree(produceData=False, compareData=True, compareDoc=False)
  be.scanTree(produceData=False, compareData=True, compareDoc=True)
  be.cleanTree()
  #use shutil to 1move data, 2copy data, 3rename file, 4rename folder
  print(be.output('Measurements'))
  print(be.outputMD5())

  ### Output including data
  print("*** FINAL HIERARCHY ***")
  print(be.outputHierarchy(False))

  ### test other functions
  print("Replication test")
  be.replicateDB(databaseName,True)

  be.exit()

except:
  print("ERROR OCCURED IN VERIFY TESTING\n"+ traceback.format_exc() )

