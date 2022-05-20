#!/usr/bin/python3
"""TEST using the FULL set of python-requirements """
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
    warnings.filterwarnings('ignore', module='js2py')

    configName = 'pasta_tutorial'
    self.be = Pasta(configName, initConfig=False)
    self.dirName = self.be.basePath
    self.be.exit(deleteDB=True)
    shutil.rmtree(self.dirName)
    os.makedirs(self.dirName)
    self.be = Pasta(configName, initViews=True, initConfig=False)

    try:
      ### CREATE PROJECTS AND SHOW
      print('*** CREATE PROJECTS AND SHOW ***')
      self.be.addData('x0', {'-name': 'Intermetals at interfaces', 'objective': 'Does spray coating lead to intermetalic phase?', 'status': 'active', 'comment': '#intermetal #Fe #Al This is a test project'})
      print(self.be.output('x0'))

      ### TEST PROJECT PLANING
      print('*** TEST PROJECT PLANING ***')
      viewProj = self.be.db.getView('viewDocType/x0')
      projID1  = [i['id'] for i in viewProj if 'Intermetals at interfaces'==i['value'][0]][0]
      self.be.changeHierarchy(projID1)
      self.be.addData('x1',    {'comment': 'This is hard! #TODO', '-name': 'Get steel and Al-powder'})
      self.be.addData('x1',    {'comment': 'This will take a long time. #WAIT', '-name': 'Get spray machine'})
      self.be.changeHierarchy(self.be.currentID)
      self.be.addData('x2',    {'-name': 'Get quotes', 'comment': 'Dont forget company-A', 'procedure': 'Guidelines of procurement'})
      self.be.addData('x2',    {'-name': 'Buy machine','comment': 'Delivery time will be 6month'})
      self.be.changeHierarchy(None)
      self.be.addData('x1',    {'-name': 'SEM images'})
      semStepID = self.be.currentID
      self.be.changeHierarchy(semStepID)
      semDirName = self.be.basePath+self.be.cwd
      self.be.changeHierarchy(None)
      self.be.addData('x1',    {'-name': 'Nanoindentation'})
      self.be.changeHierarchy(self.be.currentID)
      indentDirName = self.be.basePath+self.be.cwd
      self.be.changeHierarchy(None)
      print(self.be.outputHierarchy())

      ### TEST PROCEDURES
      print('\n*** TEST PROCEDURES ***')
      sopDir = self.dirName+os.sep+'StandardOperatingProcedures'
      os.makedirs(sopDir)
      with open(sopDir+os.sep+'Nanoindentation.org','w') as fOut:
        fOut.write('* Put sample in nanoindenter\n* Do indentation\nDo not forget to\n- calibrate tip\n- *calibrate stiffness*\n')
      with open(sopDir+os.sep+'SEM.md','w') as fOut:
        fOut.write('# Put sample in SEM\n# Do scanning\nDo not forget to\n- contact the pole-piece\n- **USE GLOVES**\n')
      self.be.addData('procedure', {'-name': 'StandardOperatingProcedures'+os.sep+'SEM.md', 'comment': '#v1'})
      self.be.addData('procedure', {'-name': 'StandardOperatingProcedures'+os.sep+'Nanoindentation.org', 'comment': '#v1'})
      print(self.be.output('procedure'))

      ### TEST SAMPLES
      print('*** TEST SAMPLES ***')
      self.be.addData('sample',    {'-name': 'AlFe cross-section', 'chemistry': 'Al99.9; FeMnCr ', 'qrCode': '13214124 99698708', 'comment': 'after OPS polishing'})
      print(self.be.output('sample'))
      print(self.be.outputQR())

      ###  TEST MEASUREMENTS AND SCANNING/CURATION
      print('*** TEST MEASUREMENTS AND SCANNING/CURATION ***')
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/Zeiss.tif', semDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', indentDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', indentDirName)
      self.be.scanTree()
      # TEST THAT LOCAL FILES/THUMBNAILS EXIST: thumbnails not created anymore
      # self.assertTrue(os.path.exists(semDirName+'Zeiss_tif_pasta.jpg'),'Zeiss PASTA not created')
      # self.assertTrue(os.path.exists(indentDirName+'1500nmXX 5 7074 -4594_txt_pasta.svg'),'Micromaterials PASTA not created')
      # self.assertTrue(os.path.exists(indentDirName+'RobinSteel0000LC_txt_pasta.svg'),'Hysitron PASTA not created')

      ### USE GLOBAL FILES
      print('*** USE GLOBAL FILES ***')
      self.be.changeHierarchy(semStepID)
      self.be.addData('measurement', {'-name': 'https://upload.wikimedia.org/wikipedia/commons/a/a4/Misc_pollen.jpg'})
      print(self.be.output('measurement'))
      # self.assertTrue(os.path.exists(semDirName+'Misc_pollen_pasta.jpg'),'Wikipedia PASTA not created')

      ### VERIFY DATABASE INTEGRITY
      print("\n*** VERIFY DATABASE INTEGRITY ***")
      print(self.be.checkDB(verbose=True))

      ### CHANGE THOSE FILES
      # sed changing file content works
      # shasum different in any case
      print("\n*** TRY TO CHANGE THOSE FILES ***")
      cmd = ['convert',semDirName+'Zeiss.tif','-fill','white','+opaque','black',semDirName+'Zeiss.tif']
      try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
      except:
        print('** COULD NOT CHANGE IMAGE Zeiss.tif')


      print('\n*** DONE WITH VERIFY ***')

    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
      self.assertTrue(False,'Exception occurred')
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()
