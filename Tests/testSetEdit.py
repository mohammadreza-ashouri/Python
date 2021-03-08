#!/usr/bin/python3
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
      self.be.addData('project', {'name': 'Intermetals at interfaces', 'objective': 'Does spray coating lead to intermetalic phase?', 'status': 'active', 'comment': '#intermetal #Fe #Al This is a test project'})

      ### TEST PROJECT PLANING
      print('*** TEST PROJECT PLANING ***')
      viewProj = self.be.db.getView('viewDocType/viewProjects')
      projID1  = [i['id'] for i in viewProj if 'Intermetals at interfaces'==i['value'][0]][0]
      self.be.changeHierarchy(projID1)
      self.be.addData('step',    {'comment': 'This is hard! #TODO', 'name': 'Get steel and Al-powder'})
      self.be.addData('step',    {'comment': 'This will take a long time. #WAIT', 'name': 'Get spray machine'})
      self.be.changeHierarchy(self.be.currentID)
      self.be.addData('task',    {'name': 'Get quotes', 'comment': 'Dont forget company-A', 'procedure': 'Guidelines of procurement'})
      self.be.addData('task',    {'name': 'Buy machine','comment': 'Delivery time will be 6month'})
      self.be.changeHierarchy(None)
      self.be.addData('step',    {'name': 'SEM images'})
      semStepID = self.be.currentID
      self.be.changeHierarchy(semStepID)
      semDirName = self.be.basePath+self.be.cwd
      self.be.changeHierarchy(None)
      self.be.addData('step',    {'name': 'Nanoindentation'})
      self.be.changeHierarchy(self.be.currentID)
      indentDirName = self.be.basePath+self.be.cwd
      self.be.changeHierarchy(None)
      oldString = self.be.outputHierarchy(False)
      print(oldString)
      print(" === STATE 0A ===\n"+self.be.checkDB(verbose=False))


      print('*** TEST MEASUREMENTS AND SCANNING/CURATION ***')
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', indentDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', indentDirName)
      self.be.scanTree()
      oldString = self.be.outputHierarchy(False)
      print(oldString)
      print(" === STATE 0B ===\n"+self.be.checkDB(verbose=False))

      print('\n*** TEST SET_EDIT_STRING: no change ***')
      myString = self.be.outputHierarchy(True,True,'tags')
      self.be.setEditString(myString)
      print(" === STATE 1A ===\n"+self.be.checkDB(verbose=False))
      myString = self.be.outputHierarchy(False,True,'tags')
      self.be.setEditString(myString)
      print(" === STATE 1B ===\n"+self.be.checkDB(verbose=False))
      myString = self.be.outputHierarchy(True,True,None)
      self.be.setEditString(myString)
      print(" === STATE 1C ===\n"+self.be.checkDB(verbose=False))
      myString = self.be.outputHierarchy(False,True,None)
      self.be.setEditString(myString)
      print(" === STATE 1D ===\n"+self.be.checkDB(verbose=False))
      newString = self.be.outputHierarchy(False)
      self.assertEqual(oldString,newString,'Hierarchy changed when should not change.')


      print('\n*** TEST SET_EDIT_STRING: change ***')
      print('Promote: Get quotes\n-----------------')
      myString = self.be.outputHierarchy(True,True,'tags')
      myString = myString.replace('** Get quotes||t-','* Get quOtes||t-')
      self.be.setEditString(myString)
      newString = self.be.outputHierarchy(True,True,None)
      print(newString)
      self.assertIn('* Get quOtes',newString,'Hierarchy did not change correctly.')
      print(" === STATE 2A ===\n"+self.be.checkDB(verbose=False))


      print('Demote: Get spray machine\n-----------------')
      myString = self.be.outputHierarchy(False,True,'tags')
      myString = myString.replace('* Get spray machine||t-','** Get spray machine||t-')
      self.be.setEditString(myString)
      newString = self.be.outputHierarchy(True,True,None)
      print(newString)
      self.assertIn('** Get spray machine',newString,'Hierarchy did not change correctly.')
      print(" === STATE 2B ===\n"+self.be.checkDB(verbose=False))

      print('Demote: SEM images\n-----------------')
      myString = self.be.outputHierarchy(True,True,None)
      myString = myString.replace('* SEM images||t-','** SEM images||t-')
      self.be.setEditString(myString)
      newString = self.be.outputHierarchy(True,True,None)
      print(newString)
      self.assertIn('** SEM images',newString,'Hierarchy did not change correctly.')
      print(" === STATE 2C ===\n"+self.be.checkDB(verbose=False))

      print('Switch measurements')
      myString = self.be.outputHierarchy(False,True,None)
      print('before:\n'+myString)
      myString = myString.split('\n')
      helper = myString[-1]
      myString[-1] = myString[-2]
      myString[-2] = helper
      myString = '\n'.join(myString)
      self.be.setEditString(myString)
      newString = self.be.outputHierarchy(False,True,None)
      print('after:\n'+newString)
      self.assertEqual(myString,newString,'Hierarchy did not change correctly.')
      print(" === STATE 2D ===\n"+self.be.checkDB(verbose=False))

      print('\n*** DONE WITH VERIFY ***')
    except:
      print('ERROR OCCURRED IN TESTING\n'+ traceback.format_exc() )
      self.assertTrue(False,'Exception occurred')
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()
