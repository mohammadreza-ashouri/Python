#!/usr/bin/python3
import os, shutil
from agileScience import AgileScience

### initialization
databaseName = 'test_db_agile_science'
dirName      = os.path.expanduser('~')+"/"+databaseName
os.makedirs( dirName, exist_ok=True )
be = AgileScience(databaseName)

### create some test projects
be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
be.addData('project', {'name': 'Test project2', 'objective': 'Test objective2', 'status': 'passive', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
be.addData('project', {'name': 'Test project3', 'objective': 'Test objective3', 'status': 'paused', 'comment': '#tag1 :field2:max: A random text'})
print(be.output('Projects'))

### create some test steps
doc = be.db.getView('viewProjects/viewProjects')
id  = [i['id'] for i in doc][0]
be.changeHierarchy(id)
be.addData('step',    {'comment': 'More random text', 'name': 'Test step one'})
be.addData('step',    {'comment': 'Much more random text', 'name': 'Test step two'})
be.addData('step',    {'comment': 'Even more random text', 'name': 'Test step three'})

### create some test tasks
doc    = be.db.getDoc(be.hierStack[-1])
id  = doc['childs'][0]
be.changeHierarchy(id)
be.addData('task',    {'name': 'Test task une', 'comment': 'A random comment', 'procedure': 'Secret potion for Asterix'})
be.addData('task',    {'name': 'Test task duo', 'comment': 'A comment', 'procedure': 'Secret potion for Obelix'})
be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})

be.changeHierarchy("step")
print(be.outputHierarchy())

### output all
print(be.output('Procedures'))
print(be.output('Samples'))
print(be.output('Measurements'))


### end of test
input("Hit enter to finish verification:")
be.db.client.delete_database(databaseName)
shutil.rmtree( dirName )
