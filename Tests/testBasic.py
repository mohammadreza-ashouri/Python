#!/usr/bin/python3
import os, shutil, traceback, sys, logging, subprocess
import warnings
import unittest
sys.path.append('/home/sbrinckm/FZJ/SourceCode/Micromechanics/src')  #allow debugging in vscode which strips the python-path
sys.path.append('/home/sbrinckm/FZJ/JamDB/Python')
from backend import JamDB

class TestStringMethods(unittest.TestCase):
  def test_main(self):
    ### MAIN ###
    # initialization: create database, destroy on filesystem and database and then create new one
    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
    warnings.filterwarnings("ignore", message="invalid escape sequence")
    warnings.filterwarnings("ignore", category=ResourceWarning, module="PIL")
    warnings.filterwarnings("ignore", category=ImportWarning)
    warnings.filterwarnings("ignore", module="js2py")

    databaseName = 'temporary_test'
    dirName      = os.path.expanduser('~')+"/"+databaseName
    shutil.rmtree(dirName)
    os.makedirs(dirName)
    self.be = JamDB(databaseName)
    self.be.exit(deleteDB=True)
    self.be = JamDB(databaseName)

    try:
      ### create some projects and show them
      print("*** TEST PROJECTS ***")
      self.be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
      self.be.addData('project', {'name': 'Test project2', 'objective': 'Test objective2', 'status': 'passive', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
      self.be.addData('project', {'name': 'Test project3', 'objective': 'Test objective3', 'status': 'paused', 'comment': '#tag1 :field2:max: A random text'})
      print(self.be.output('Projects'))

      ### create some steps and tasks in the first (by id-number) project
      # add also some empty measurements
      print("*** TEST PROJECT HIERARCHY: no output ***")
      viewProj = self.be.db.getView('viewProjects/viewProjects')
      projID  = [i['id'] for i in viewProj][0]
      self.be.changeHierarchy(projID)
      projDirName = self.be.basePath+self.be.cwd
      self.be.addData('step',    {'comment': 'More random text', 'name': 'Test step one'})
      self.be.addData('step',    {'comment': 'Much more random text', 'name': 'Test step two'})
      stepID = self.be.currentID
      self.be.addData('step',    {'comment': 'Even more random text', 'name': 'Test step three'})
      self.be.changeHierarchy(stepID)
      self.be.addData('task',    {'name': 'Test task une', 'comment': 'A random comment', 'procedure': 'Secret potion for Asterix'})
      self.be.addData('task',    {'name': 'Test task duo', 'comment': 'A comment', 'procedure': 'Secret potion for Obelix'})
      self.be.changeHierarchy(self.be.currentID)  #cd in task
      self.be.addData('measurement', {'name': 'geolocation.txt', 'comment': 'Center of work'})
      self.be.addData('measurement', {'name': "https://i.picsum.photos/id/237/200/300.jpg", 'comment': 'logo'})
      self.be.changeHierarchy(None)  #cd .. into step
      self.be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})

      ### output of project
      print("\n*** TEST OUTPUT OF INITIAL STRUCTURE ***")
      self.be.changeHierarchy(None) #cd .. into a project
      print("Current directory:",self.be.cwd)
      print(self.be.outputHierarchy())

      ### edit project
      print("\n*** TEST EDIT PROJECT ***")
      self.be.addData('-edit-', {'comment': '#tag1 A random text plus edition\n'})
      myString = self.be.getEditString()
      myString = myString.replace('* Test step two: t-','** Test step two: t-')
      self.be.setEditString(myString)
      self.be.scanTree()  #nothing done: no harm

      ### Procedures
      print("\n*** TEST PROCEDURES ***")
      self.be.addData('procedure', {'name': 'Test procedure 1', 'content': '1. grind, 2. polish, 3. microscope', 'comment': ''})
      self.be.addData('procedure', {'name': 'Test procedure 2', 'content': '1. grind, 2. microscope', 'comment': ''})
      self.be.addData('procedure', {'name': 'Test procedure 3', 'content': '1. polish, 2. microscope', 'comment': ''})
      self.be.changeHierarchy(None) #cd .. into root, to create procedure without project. Should not be done, but no harm
      self.be.addData('procedure', {'name': 'Test procedure without project', 'content': 'Secret potion for Asterix', 'comment': ''})
      print(self.be.output('Procedures'))

      ### Samples
      print("*** TEST SAMPLES ***")
      self.be.changeHierarchy(projID)
      self.be.addData('sample',    {'name': 'Big copper block', 'chemistry': 'Cu99.999', 'qr_code': '13214124 12341234', 'comment': '#save'})
      self.be.addData('sample',    {'name': 'Small copper block', 'chemistry': 'Cu99.99999', 'qr_code': '13214124111', 'comment': ''})
      self.be.addData('sample',    {'name': 'Big iron ore', 'chemistry': 'Fe', 'qr_code': '1321412411', 'comment': ''})
      self.be.addData('sample',    {'name': 'Ahoj-Brause Pulver', 'chemistry': '???', 'qr_code': '', 'comment': ''})
      self.be.addData('sample',    {'name': 'Gummibären', 'chemistry': '???', 'qr_code': '', 'comment': '6 pieces'})
      self.be.addData('sample',    {'name': 'Lutscher', 'chemistry': '???', 'qr_code': '', 'comment': ''})
      self.be.addData('sample',    {'name': 'Taschentücher', 'chemistry': '???', 'qr_code': '', 'comment': ''})
      print(self.be.output('Samples'))
      print(self.be.outputQR())

      ### Add measurements by copying from somewhere into tree
      # also enter empty data to test if tags are extracted
      # scan tree to register into database
      print("*** TEST MEASUREMENTS AND SCANNING 1 ***")
      self.be.addData('measurement', {'name': 'filename.txt', 'comment': '#random #5 great stuff'})
      self.be.addData('measurement', {'name': 'filename.jpg', 'comment': '#3 #other medium stuff'})
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/Zeiss.tif', projDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', projDirName)
      stepDirName = self.be.basePath+self.be.db.getDoc(stepID)['branch'][0]['path']
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', stepDirName)
      self.be.scanTree()

      ### Change plot-type
      viewMeasurements = self.be.db.getView('viewMeasurements/viewMeasurements')
      for item in viewMeasurements:
        fileName = item['value'][0]
        if fileName == 'Zeiss.tif':
          hierStack = [ item['id'] ]
          doc = self.be.getDoc(item['id'])
          newType = doc['type']+['maximum Contrast']
          fullPath= doc['branch'][0]['path'] #here choose first branch, but other are possible
          self.be.addData('-edit-', {'type':newType, 'name':fullPath}, hierStack=hierStack, forceNewImage=True)

      ### Try to fool system: move directory that includes data to another random name
      print("*** TEST MEASUREMENTS AND SCANNING 2 ***")
      origin = self.be.basePath+self.be.db.getDoc(stepID)['branch'][0]['path']
      target = os.sep.join(origin.split(os.sep)[:-1])+os.sep+"RandomDir"
      shutil.move(origin, target)
      self.be.scanTree()

      ### Move data, copy data into different project
      print("*** TEST MEASUREMENTS AND SCANNING 3 ***")
      projID1  = [i['id'] for i in viewProj][1]
      self.be.changeHierarchy(projID1) #change into non-existant path; try to confuse software
      self.be.changeHierarchy(None)
      self.be.changeHierarchy(projID1) #change into existant path
      projDirName1 = self.be.basePath+self.be.cwd
      shutil.copy(projDirName+'/Zeiss.tif',projDirName1+'/Zeiss.tif')
      shutil.move(projDirName+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteel0000LC.txt')
      self.be.scanTree()

      ### Try to fool system: rename file
      # verify database and filesystem into fileVerify
      # produce database entries into filesystem
      # compare database entries to those in filesystem (allows to check for unforseen events)
      # clean all that database entries in the filesystem
      print("*** TEST MEASUREMENTS AND SCANNING 4 ***")
      shutil.move(projDirName1+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteelLC.txt')
      self.be.scanTree()  #always scan before produceData: ensure that database correct
      self.fileVerify(1,'=========== Before ===========')
      self.be.scanTree('produceData')
      self.fileVerify(2,'=========== After ===========')  #use diff-file to compare hierarchies, directory tree
      self.be.scanTree('compareToDB')
      self.be.cleanTree()

      ### Output all the measurements and changes until now
      # output MD5-sum
      print("*** TEST MEASUREMENTS AND SCANNING 3 ***")
      print(self.be.output('Measurements'))
      print(self.be.outputMD5())

      ### Output including data: change back into folder that has content
      print("*** FINAL HIERARCHY ***")
      self.be.changeHierarchy(None)
      self.be.changeHierarchy(projID)
      print(self.be.outputHierarchy(False))

      ### check consistency of database and replicate to global server
      print("\n*** Check this database ***")
      print(self.be.checkDB())
      print("Replication test")
      self.be.replicateDB(databaseName,True)
      print("\n*** DONE WITH VERIFY ***")
    except:
      print("ERROR OCCURRED IN VERIFY TESTING\n"+ traceback.format_exc() )
    return


  def tearDown(self):
    self.be.exit()
    return


  def fileVerify(self,number, text, onlyHierarchy=True):
    """
    use diff-file to compare hierarchies, directory tree
    """
    with open(self.be.softwarePath+'/Tests/verify'+str(number)+'.org','w') as f:
      f.write(text)
      f.write("++STATE: "+self.be.cwd+" "+str(self.be.hierStack)+"\n")
      f.write(self.be.outputHierarchy(onlyHierarchy,True,'all'))
      f.write("\n====================")
      f.write(subprocess.run(['tree'], stdout=subprocess.PIPE).stdout.decode('utf-8'))
    logging.info(text)
    return

if __name__ == '__main__':
  unittest.main()
