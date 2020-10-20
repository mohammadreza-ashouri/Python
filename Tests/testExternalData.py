#!/usr/bin/python3
"""
TEST IF EXTERNAL DATA CAN BE READ,...
"""
import os, shutil, traceback, time
import warnings, subprocess
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

    configName = 'develop_test0'
    dirName    = 'temporary_test0'
    self.dirName      = os.path.expanduser('~')+os.sep+dirName
    if os.path.exists(self.dirName): shutil.rmtree(self.dirName)
    os.makedirs(self.dirName)
    self.be = JamDB(configName)
    self.be.exit(deleteDB=True)
    self.be = JamDB(configName)

    try:
      ### create some project and move into it
      self.be.addData('project', {'name': 'Test project1', 'objective': 'Test objective1', 'status': 'active', 'comment': '#tag1 #tag2 :field1:1: :field2:max: A random text'})
      viewProj = self.be.db.getView('viewProjects/viewProjects')
      projID  = [i['id'] for i in viewProj][0]
      self.be.changeHierarchy(projID)

      ### add external data
      self.be.addData('measurement', {'name': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png', 'comment': 'small'}, localCopy=True)
      self.be.addData('measurement', {'name': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/640px-Google_2015_logo.svg.png', 'comment': 'large'})
      projDirName = self.be.basePath+self.be.cwd
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/Zeiss.tif', projDirName)
      self.be.scanTree()
      print(self.be.output('Measurements'))
      print(self.be.outputMD5())

      ### check consistency of database and replicate to global server
      print('\n*** Check this database ***')
      output = self.be.checkDB()
      print(output)
      self.assertTrue(output.count('**UNSURE')==0,'UNSURE string in output')
      self.assertTrue(output.count('**WARNING')==0,'WARNING string in output')
      self.assertTrue(output.count('**ERROR')==0,'ERROR string in output')
      print('\n*** DONE WITH VERIFY ***')
    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
    return


  def tearDown(self):
    try:
      self.be.exit(deleteDB=True)
    except:
      pass
    time.sleep(2)
    if os.path.exists(self.dirName):
      #uninit / delete everything of git-annex and datalad
      curDirectory = os.path.curdir
      os.chdir(self.dirName)
      for iDir in os.listdir('.'):
        os.chdir(iDir)
        output = subprocess.run(['git-annex','uninit'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.chdir('..')
      os.chdir(curDirectory)
      #remove directory
      shutil.rmtree(self.dirName)
    return

if __name__ == '__main__':
  unittest.main()
