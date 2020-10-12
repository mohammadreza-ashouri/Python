#!/usr/bin/python3
import os, shutil, traceback, logging, subprocess
import warnings
import unittest
from backend import JamDB

class TestStringMethods(unittest.TestCase):
  def test_main(self):
    ### MAIN ###
    # initialization: create database, destroy on filesystem and database and then create new one
    warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
    warnings.filterwarnings('ignore', message='invalid escape sequence')
    warnings.filterwarnings('ignore', category=ResourceWarning, module='PIL')
    warnings.filterwarnings('ignore', category=ImportWarning)
    warnings.filterwarnings('ignore', module='js2py')

    configName = 'develop_test'
    dirName      = os.path.expanduser('~')+os.sep+configName
    if os.path.exists(dirName): shutil.rmtree(dirName)
    os.makedirs(dirName)
    self.be = JamDB(configName)
    self.be.exit(deleteDB=True)
    self.be = JamDB(configName)

    try:
      ### create some projects and show them
      print('*** TEST PROJECTS ***')
      self.be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
      self.be.addData('project', {'name': 'Test project2', 'objective': 'Test objective2', 'status': 'passive', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
      self.be.addData('project', {'name': 'Test project3', 'objective': 'Test objective3', 'status': 'paused', 'comment': '#tag1 :field2:max: A random text'})
      print(self.be.output('Projects'))

      ### create some steps and tasks in the first (by id-number) project
      # add also some empty measurements
      print('*** TEST PROJECT HIERARCHY: no output ***')
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
      self.be.addData('measurement', {'name': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png', 'comment': 'logo'})
      self.be.changeHierarchy(None)  #cd .. into step
      self.be.addData('task',    {'name': 'Test task tres', 'comment': 'A long comment', 'procedure': 'Secret potion for all'})

      ### output of project
      print('\n*** TEST OUTPUT OF INITIAL STRUCTURE ***')
      self.be.changeHierarchy(None) #cd .. into a project
      print('Current directory:',self.be.cwd)
      print(self.be.outputHierarchy())

      ### edit project: easy and setEditString
      print('\n*** TEST EDIT PROJECT ***')
      self.be.addData('-edit-', {'comment': '#tag1 A random text plus edition\n'})
      myString = self.be.getEditString()
      myString = myString.replace('* Test step two||t-','** Test step two||t-')
      myString+= '\n* Test step four\nTags: #SomeBody\n- One line of list\n- Two lines of list\n  - One sublist\n'
      self.be.setEditString(myString)
      self.be.scanTree()  #nothing done: no harm
      print(self.be.outputHierarchy())

      ### Procedures
      print('\n*** TEST PROCEDURES ***')
      self.be.addData('procedure', {'name': 'Test procedure 1', 'content': '1. grind, 2. polish, 3. microscope', 'comment': ''})
      self.be.addData('procedure', {'name': 'Test procedure 2', 'content': '1. grind, 2. microscope', 'comment': ''})
      self.be.addData('procedure', {'name': 'Test procedure 3', 'content': '1. polish, 2. microscope', 'comment': ''})
      self.be.changeHierarchy(None) #cd .. into root, to create procedure without project. Should not be done, but no harm
      self.be.addData('procedure', {'name': 'Test procedure without project', 'content': 'Secret potion for Asterix', 'comment': ''})
      print(self.be.output('Procedures'))

      ### Samples
      print('*** TEST SAMPLES ***')
      self.be.changeHierarchy(projID)
      self.be.addData('sample',    {'name': 'Big copper block', 'chemistry': 'Cu99.999', 'qrCode': '13214124 12341234', 'comment': '#save'})
      self.be.addData('sample',    {'name': 'Small copper block', 'chemistry': 'Cu99.99999', 'qrCode': '13214124111', 'comment': ''})
      self.be.addData('sample',    {'name': 'Big iron ore', 'chemistry': 'Fe', 'qrCode': '1321412411', 'comment': ''})
      self.be.addData('sample',    {'name': 'Ahoj-Brause Pulver', 'chemistry': '???', 'qrCode': '', 'comment': ''})
      self.be.addData('sample',    {'name': 'Gummibären', 'chemistry': '???', 'qrCode': '', 'comment': '6 pieces'})
      self.be.addData('sample',    {'name': 'Lutscher', 'chemistry': '???', 'qrCode': '', 'comment': ''})
      self.be.addData('sample',    {'name': 'Taschentücher', 'chemistry': '???', 'qrCode': '', 'comment': ''})
      print(self.be.output('Samples'))
      print(self.be.outputQR())

      ### Add measurements by copying from somewhere into tree
      # also enter empty data to test if tags are extracted
      # scan tree to register into database
      print('*** TEST MEASUREMENTS AND SCANNING 1 ***')
      self.be.addData('measurement', {'name': 'filename.txt', 'comment': '#random #5 great stuff'})
      self.be.addData('measurement', {'name': 'filename.jpg', 'comment': '#3 #other medium stuff'})
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/Zeiss.tif', projDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', projDirName)
      stepDirName = self.be.basePath+self.be.db.getDoc(stepID)['branch'][0]['path']
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', stepDirName)
      self.be.scanTree()

      ### edit project to test if path of sub-measurements are adopted
      print('\n*** TEST EDIT PROJECT AGAIN: back from previous version ***')
      self.fileVerify(1,'=========== Before ===========')
      myString = self.be.getEditString()
      myString = myString.replace('** Test step two||t-','* Test step two||t-')
      self.be.setEditString(myString)
      self.fileVerify(2,'=========== After  ===========')  #use diff-file to compare hierarchies, directory tree

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
      print('*** TEST MEASUREMENTS AND SCANNING 2 ***')
      origin = self.be.basePath+self.be.db.getDoc(stepID)['branch'][0]['path']
      target = os.sep.join(origin.split(os.sep)[:-1])+os.sep+'RandomDir'
      shutil.move(origin, target)
      self.be.scanTree()

      ### Move data, copy data into different project
      print('*** TEST MEASUREMENTS AND SCANNING 3 ***')
      projID1  = [i['id'] for i in viewProj][1]
      print('Change into non-existant path')
      self.be.changeHierarchy(projID1) #change into non-existant path; try to confuse software
      self.be.changeHierarchy(None)
      self.be.changeHierarchy(projID1) #change into existant path
      projDirName1 = self.be.basePath+self.be.cwd
      shutil.copy(projDirName+'/Zeiss.tif',projDirName1+'/Zeiss.tif')
      shutil.move(projDirName+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteel0000LC.txt')
      self.be.scanTree()

      ### Remove data: adopt branch in document
      print('*** TEST MEASUREMENTS AND SCANNING 3.1 ***')
      os.remove(projDirName1+'/Zeiss.tif')
      self.be.scanTree()

      ### Try to fool system: rename file
      # verify database and filesystem into fileVerify
      # produce database entries into filesystem
      # compare database entries to those in filesystem (allows to check for unforseen events)
      # clean all that database entries in the filesystem
      print('*** TEST MEASUREMENTS AND SCANNING 4 ***')
      shutil.move(projDirName1+'/RobinSteel0000LC.txt',projDirName1+'/RobinSteelLC.txt')
      self.be.scanTree()  #always scan before produceData: ensure that database correct

      ### Output all the measurements and changes until now
      # output MD5-sum
      print('*** TEST MEASUREMENTS AND SCANNING 3 ***')
      print(self.be.output('Measurements'))
      print(self.be.outputMD5())

      ### Output including data: change back into folder that has content
      print('*** FINAL HIERARCHY ***')
      self.be.changeHierarchy(None)
      self.be.changeHierarchy(projID)
      print(self.be.outputHierarchy(False))

      ### check consistency of database and replicate to global server
      print('\n*** Check this database ***')
      output = self.be.checkDB()
      print(output)
      self.assertTrue(output.count('**UNSURE')==0,'UNSURE string in output')
      self.assertTrue(output.count('**WARNING')==0,'WARNING string in output')
      self.assertTrue(output.count('**ERROR')==0,'ERROR string in output')
      print('Replication test')
      self.be.replicateDB(configName,True)
      print('\n*** DONE WITH VERIFY ***')
      self.backup()
    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
    return


  def backup(self):
    print("BACKUP TEST")
    if os.path.exists(self.be.basePath+'jamDB_backup.zip'):
      os.unlink(self.be.basePath+'jamDB_backup.zip')
    warnings.simplefilter("ignore")
    self.be.backup() #throws an "Exception ignored in SSL Socket"
    warnings.simplefilter("default")
    if not os.path.exists(self.be.basePath+'jamDB_backup.zip'):
      print("Backup did not create zip file",self.be.basePath+'jamDB_backup.zip')
      raise NameError('zip file was not created')
    success = self.be.backup('compare')
    if not success:
      print('Backup comparison unsuccessful')
      raise NameError('Backup comparison failed')
    success = self.be.backup('restore')
    if not success:
      print('Backup comparison unsuccessful')
      raise NameError('Backup comparison failed')
    return


  def tearDown(self):
    try:
      self.be.exit()
      with open(self.be.softwarePath+'/jamDB.log','r') as fIn:
        text = fIn.read()
        self.assertFalse(text.count('**WARNING')==7,'WARNING string !=7 in log-file')
        self.assertFalse('ERROR:' in text  ,'ERROR string in log-file')
    except:
      pass
    return


  def fileVerify(self,number, text, onlyHierarchy=True):
    """
    use diff-file to compare hierarchies, directory tree
    """
    with open(self.be.softwarePath+'/Tests/verify'+str(number)+'.org','w') as f:
      f.write(text)
      f.write('++STATE: '+self.be.cwd+' '+str(self.be.hierStack)+'\n')
      f.write(self.be.outputHierarchy(onlyHierarchy,True,'all'))
      f.write('\n====================')
      try:
        f.write(subprocess.run(['tree'], stdout=subprocess.PIPE).stdout.decode('utf-8'))
      except:
        f.write("No tree command installed")
    print("Did ",text)
    return

if __name__ == '__main__':
  unittest.main()