#!/usr/bin/python3
import os, shutil, traceback
from agileScience import AgileScience

### initialization
databaseName = 'agile_science'
dirName      = os.path.expanduser('~')+"/"+databaseName
os.makedirs(dirName, exist_ok=True)
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
  projDirName = be.getDoc(projID)['dirName']
  be.changeHierarchy(projID)
  be.addData('step',    {'comment': 'More random text', 'name': 'Test step one'})
  be.addData('step',    {'comment': 'Much more random text', 'name': 'Test step two'})
  be.addData('step',    {'comment': 'Even more random text', 'name': 'Test step three'})
  doc    = be.getDoc(be.hierStack[-1])
  stepID  = doc['childs'][0]
  be.changeHierarchy(stepID)
  be.addData('task',    {'name': 'Test task une', 'comment': 'A random comment', 'procedure': 'Secret potion for Asterix'})
  be.addData('task',    {'name': 'Test task duo', 'comment': 'A comment', 'procedure': 'Secret potion for Obelix'})
  be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})
  be.changeHierarchy(None)
  print(be.outputHierarchy())

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
  print("*** TEST MEASUREMENTS ***")
  be.addData('measurement', {'name': 'filename.txt', 'comment': '#random #5 great stuff'})
  be.addData('measurement', {'name': 'filename.jpg', 'comment': '#3 #other medium stuff'})
  shutil.copy(be.softwareDirectory+'/ExampleMeasurements/Zeiss.tif', dirName+'/'+projDirName+'/')
  shutil.copy(be.softwareDirectory+'/ExampleMeasurements/RobinSteel0000LC.txt', dirName+'/'+projDirName+'/')
  be.scanDirectory()
  be.scanDirectory()
  print(be.output('Measurements'))
  print(be.outputMD5())

  ### test other functions
  print("Replication test")
  be.replicateDB()

except:
  print("ERROR OCCURED IN VERIFY TESTING\n"+ traceback.format_exc() )

### end of test
answer = input("Clean all [y/N]: ")
if answer=='y':
  be.db.client.delete_database(databaseName)
  shutil.rmtree(dirName)
  os.remove('/home/sbrinckm/FZJ/AgileScience/Python/jams.log')
be.exit()
