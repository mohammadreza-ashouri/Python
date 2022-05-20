#!/usr/bin/python3
"""TEST using the MINIMAL set of python-requirements and run after installation
This test is HAS TO BE skiped during checkAllVersions since it resets everything
"""
import os, shutil, traceback, logging, subprocess
import warnings, json
import unittest
from backend import Pasta

class TestStringMethods(unittest.TestCase):
  def test_main(self):
    ### MAIN ###
    # initialization: create database, destroy on filesystem and database and then create new one
    warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
    warnings.filterwarnings('ignore', message='invalid escape sequence')
    warnings.filterwarnings('ignore', category=ResourceWarning, module='PIL')
    warnings.filterwarnings('ignore', category=ImportWarning)

    reply = input("Do you really want to continue: This will delete things! [y/N] ")
    if reply != 'y':
      return



    configName = 'research'
    self.be = Pasta(configName, initConfig=False)
    self.dirName = self.be.basePath
    self.be.exit(deleteDB=True)
    shutil.rmtree(self.dirName)
    os.makedirs(self.dirName)
    self.be = Pasta(configName, initViews=True, initConfig=False)

    try:
      ### CREATE PROJECTS AND SHOW
      print('*** CREATE EXAMPLE PROJECT AND SHOW ***')
      self.be.addData('x0', {'-name': "PASTA's Example Project", 'objective': 'Test if everything is working as intended.', 'status': 'active', 'comment': '#tag Can be used as reference or deleted'})
      print(self.be.output('x0'))

      ### TEST PROJECT PLANING
      print('*** TEST PROJECT PLANING ***')
      viewProj = self.be.db.getView('viewDocType/x0')
      projID1  = [i['id'] for i in viewProj if 'PASTA' in i['value'][0]][0]
      self.be.changeHierarchy(projID1)
      self.be.addData('x1',    {'comment': 'This is hard! #TODO', '-name': 'This is an example task'})
      self.be.addData('x1',    {'comment': 'This will take a long time. #WAIT', '-name': 'This is another example task'})
      self.be.changeHierarchy(self.be.currentID)
      self.be.addData('x2',    {'-name': 'This is an example subtask',     'comment': 'Random comment 1'})
      self.be.addData('x2',    {'-name': 'This is another example subtask','comment': 'Random comment 2'})
      self.be.changeHierarchy(None)
      self.be.addData('x1',    {'-name': 'Data files'})
      semStepID = self.be.currentID
      self.be.changeHierarchy(semStepID)
      semDirName = self.be.basePath+self.be.cwd
      self.be.changeHierarchy(None)
      print(self.be.outputHierarchy())

      ### TEST PROCEDURES
      print('\n*** TEST PROCEDURES ***')
      sopDir = self.dirName+os.sep+'StandardOperatingProcedures'
      os.makedirs(sopDir)
      with open(sopDir+os.sep+'Example_SOP.md','w') as fOut:
        fOut.write('# Put sample in instrument\n# Do something\nDo not forget to\n- not do anything wrong\n- **USE BOLD LETTERS**\n')
      self.be.addData('procedure', {'-name': 'StandardOperatingProcedures'+os.sep+'Example_SOP.md', 'comment': '#v1'})
      print(self.be.output('procedure'))

      ### TEST SAMPLES
      print('*** TEST SAMPLES ***')
      self.be.addData('sample',    {'-name': 'Example sample', 'chemistry': 'A2B2C3', 'qrCode': '13214124 99698708', 'comment': 'can be used as example or removed'})
      print(self.be.output('sample'))
      print(self.be.outputQR())

      ###  TEST MEASUREMENTS AND SCANNING/CURATION
      print('*** TEST MEASUREMENTS AND SCANNING/CURATION ***')
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/simple.png', semDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/simple.csv', semDirName)
      self.be.scanTree()

      ### USE GLOBAL FILES
      print('*** USE GLOBAL FILES ***')
      self.be.changeHierarchy(semStepID)
      self.be.addData('measurement', {'-name': 'https://developers.google.com/search/mobile-sites/imgs/mobile-seo/separate-urls.png', 'comment':'remote image from google. Used for testing and reference. Can be deleted.'})
      print(self.be.output('measurement'))

      ### VERIFY DATABASE INTEGRITY
      print("\n*** VERIFY DATABASE INTEGRITY ***")
      print(self.be.checkDB(verbose=True))

      print('\n*** DONE WITH VERIFY ***')

    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
      self.assertTrue(False,'Exception occurred')
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()
