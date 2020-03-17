#!/usr/bin/python3
import os, shutil
from agileScience import AgileScience

### initialization
databaseName = 'test_db_agile_science'
dirName      = os.path.expanduser('~')+"/"+databaseName
os.makedirs(dirName, exist_ok=True)
be = AgileScience(databaseName)

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
be.addData('sample',    {'name': 'Big copper block', 'chemistry': 'Cu99.999', 'qr_code': '13214124', 'comment': '#save'})
be.addData('sample',    {'name': 'Small copper block', 'chemistry': 'Cu99.99999', 'qr_code': '13214124111', 'comment': ''})
be.addData('sample',    {'name': 'Big iron ore', 'chemistry': 'Fe', 'qr_code': '1321412411', 'comment': ''})
print(be.output('Samples'))

### test measurements
print("*** TEST MEASUREMENTS ***")
be.addData('measurement', {'name': 'filename.txt', 'alias': '', 'comment': '#5 great stuff'})
be.addData('measurement', {'name': 'filename.jpg', 'alias': 'image', 'comment': '#3 medium stuff'})
shutil.copy(be.softwareDirectory+'/ExampleMeasurements/Zeiss.tif', dirName+'/TestProject1/')
shutil.copy(be.softwareDirectory+'/ExampleMeasurements/RobinSteel0000LC.txt', dirName+'/TestProject1/')
be.scanDirectory()
print(be.output('Measurements'))

### test other functions
print("Skip replication test since authentication does not seem to work on remote host")
# be.replicateDB(databaseName)

### end of test
input("Hit enter to finish verification:")
be.db.client.delete_database(databaseName)
shutil.rmtree(dirName)
be.exit()
