#!/usr/bin/python3
import os, shutil, traceback, sys, logging, subprocess
from backend import JamDB

def fileVerify(number, text, onlyHierarchy=True):
  """
  use diff-file to compare hierarchies, directory tree
  """
  with open(be.softwarePath+'/verify'+str(number)+'.org','w') as f:
    f.write(text)
    f.write("++STATE: "+be.cwd+" "+str(be.hierStack)+"\n")
    f.write(be.outputHierarchy(onlyHierarchy,True,'all'))
    f.write("\n====================")
    f.write(subprocess.run(['tree'], stdout=subprocess.PIPE).stdout.decode('utf-8'))
  logging.info(text)


### MAIN ###
# initialization: create database, destroy on filesystem and database and then create new one
sys.path.append('/home/sbrinckm/FZJ/SourceCode/Micromechanics/src')  #allow debugging in vscode which strips the python-path
databaseName = 'temporary_test'
dirName      = os.path.expanduser('~')+"/"+databaseName
shutil.rmtree(dirName)
os.makedirs(dirName)
be = JamDB(databaseName)
be.exit(deleteDB=True)
be = JamDB(databaseName)

try:
  ### create some projects and show them
  print("*** TEST PROJECTS ***")
  be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
  be.addData('project', {'name': 'Test project2', 'objective': 'Test objective2', 'status': 'passive', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
  be.addData('project', {'name': 'Test project3', 'objective': 'Test objective3', 'status': 'paused', 'comment': '#tag1 :field2:max: A random text'})
  print(be.output('Projects'))

  ### create some steps and tasks in the first (by id-number) project
  # add also some empty measurements
  print("*** TEST PROJECT HIERARCHY: no output ***")
  doc = be.db.getView('viewProjects/viewProjects')
  projID  = [i['id'] for i in doc][0]
  be.changeHierarchy(projID)
  projDirName = be.basePath+be.cwd
  be.addData('step',    {'comment': 'More random text', 'name': 'Test step one'})
  be.addData('step',    {'comment': 'Much more random text', 'name': 'Test step two'})
  stepID = be.currentID
  be.addData('step',    {'comment': 'Even more random text', 'name': 'Test step three'})
  be.changeHierarchy(stepID)
  be.addData('task',    {'name': 'Test task une', 'comment': 'A random comment', 'procedure': 'Secret potion for Asterix'})
  be.addData('task',    {'name': 'Test task duo', 'comment': 'A comment', 'procedure': 'Secret potion for Obelix'})
  be.changeHierarchy(be.currentID)  #cd in task
  be.addData('measurement', {'name': 'geolocation.txt', 'comment': 'Center of work'})
  #TODO be.addData('measurement', {'name': "https://www.fz-juelich.de/SiteGlobals/StyleBundles/Bilder/NeuesLayout/logo.jpg", 'comment': 'logo'})
  be.changeHierarchy(None)  #cd .. into step
  be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})

  ### output of project
  print("\n*** TEST OUTPUT OF INITIAL STRUCTURE ***")
  be.changeHierarchy(None) #cd .. into a project
  print(be.cwd) #TODO change to be.printHierarchy
  print(be.outputHierarchy())

  ### edit project
  print("\n*** TEST EDIT PROJECT ***")
  be.addData('-edit-', {'comment': '#tag1 A random text plus edition\n'})
  myString = be.getEditString()
  myString = myString.replace('* Test step two: t-','** Test step two: t-')
  be.setEditString(myString)
  be.scanTree()  #nothing done: no harm

  ### Procedures
  print("\n*** TEST PROCEDURES ***")
  be.addData('procedure', {'name': 'Test procedure 1', 'content': '1. grind, 2. polish, 3. microscope', 'comment': ''})
  be.addData('procedure', {'name': 'Test procedure 2', 'content': '1. grind, 2. microscope', 'comment': ''})
  be.addData('procedure', {'name': 'Test procedure 3', 'content': '1. polish, 2. microscope', 'comment': ''})
  be.changeHierarchy(None) #cd .. into root, to create procedure without project. Should not be done, but no harm
  be.addData('procedure', {'name': 'Test procedure without project', 'content': 'Secret potion for Asterix', 'comment': ''})
  print(be.output('Procedures'))

  ### Samples
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

  ### Add measurements by copying from somewhere into tree
  # also enter empty data to test if tags are extracted
  # scan tree to register into database
  print("*** TEST MEASUREMENTS AND SCANNING 1 ***")
  be.addData('measurement', {'name': 'filename.txt', 'comment': '#random #5 great stuff'})
  be.addData('measurement', {'name': 'filename.jpg', 'comment': '#3 #other medium stuff'})
  shutil.copy(be.softwarePath+'/ExampleMeasurements/Zeiss.tif', projDirName)
  shutil.copy(be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', projDirName)
  stepDirName = be.basePath+be.db.getDoc(stepID)['branch'][0]['path']
  shutil.copy(be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', stepDirName)
  be.scanTree()

  ### Try to fool system: move directory that includes data to another random name
  print("*** TEST MEASUREMENTS AND SCANNING 2 ***")
  origin = be.basePath+be.db.getDoc(stepID)['branch'][0]['path']
  target = os.sep.join(origin.split(os.sep)[:-1])+os.sep+"RandomDir"
  shutil.move(origin, target)
  be.scanTree()

  ### Move data, copy data into different project
  print("*** TEST MEASUREMENTS AND SCANNING 3 ***")
  projID1  = [i['id'] for i in doc][1]
  be.changeHierarchy(projID1) #change into non-existant path; try to confuse software
  be.changeHierarchy(None)
  be.changeHierarchy(projID1) #change into existant path
  projDirName1 = be.basePath+be.cwd
  shutil.copy(projDirName+'/Zeiss.tif',projDirName1+'/Zeiss.tif')
  shutil.move(projDirName+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteel0000LC.txt')
  be.scanTree()

  ### Try to fool system: rename file
  # verify database and filesystem into fileVerify
  # produce database entries into filesystem
  # compare database entries to those in filesystem (allows to check for unforseen events)
  # clean all that database entries in the filesystem
  print("*** TEST MEASUREMENTS AND SCANNING 4 ***")
  shutil.move(projDirName1+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteelLC.txt')
  be.scanTree()  #always scan before produceData: ensure that database correct
  fileVerify(1,'=========== Before ===========')
  be.scanTree('produceData')
  fileVerify(2,'=========== After ===========')  #use diff-file to compare hierarchies, directory tree
  be.scanTree('compareToDB')
  be.cleanTree()

  ### Output all the measurements and changes until now
  # output MD5-sum
  print("*** TEST MEASUREMENTS AND SCANNING 3 ***")
  print(be.output('Measurements'))
  print(be.outputMD5())

  ### Output including data: change back into folder that has content
  print("*** FINAL HIERARCHY ***")
  be.changeHierarchy(None)
  be.changeHierarchy(projID)
  print(be.outputHierarchy(False))

  ### check consistency of database and replicate to global server
  print("\n*** Check this database ***")
  print(be.checkDB())
  print("Replication test")
  be.replicateDB(databaseName,True)

  print("\n*** DONE WITH VERIFY ***")
  be.exit()

except:
  print("ERROR OCCURRED IN VERIFY TESTING\n"+ traceback.format_exc() )

