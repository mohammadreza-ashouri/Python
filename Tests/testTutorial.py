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

    configName = 'jams_tutorial'
    dirName    = 'jams_tutorial'
    self.dirName      = os.path.expanduser('~')+os.sep+dirName
    if os.path.exists(self.dirName):
      #uninit / delete everything of git-annex and datalad
      curDirectory = os.path.curdir
      os.chdir(self.dirName)
      for iDir in os.listdir('.'):
        if not os.path.isdir(iDir):
          continue
        os.chdir(iDir)
        output = subprocess.run(['git-annex','uninit'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.chdir('..')
      os.chdir(curDirectory)
      #remove directory
      shutil.rmtree(self.dirName)
    os.makedirs(self.dirName)
    self.be = JamDB(configName)
    self.be.exit(deleteDB=True)
    self.be = JamDB(configName)

    try:
      ### CREATE PROJECTS AND SHOW
      print('*** CREATE PROJECTS AND SHOW ***')
      self.be.addData('project', {'name': 'Intermetals at interfaces', 'objective': 'Does spray coating lead to intermetalic phase?', 'status': 'active', 'comment': '#intermetal #Fe #Al This is a test project'})
      self.be.addData('project', {'name': 'Surface evolution in tribology', 'objective': 'Why does the surface get rough during tribology?', 'status': 'passive', 'comment': '#tribology The answer is obvious'})
      self.be.addData('project', {'name': 'Steel', 'objective': 'Test strength of steel', 'status': 'paused', 'comment': '#Fe Obvious example without answer'})
      print(self.be.output('Projects'))


      ### TEST PROJECT PLANING
      print('*** TEST PROJECT PLANING ***')
      viewProj = self.be.db.getView('viewProjects/viewProjects')
      projID1  = [i['id'] for i in viewProj if 'Intermetals at interfaces'==i['value'][0]][0]
      self.be.changeHierarchy(projID1)
      self.be.addData('step',    {'comment': 'This is hard!', 'name': 'Get steel and Al-powder'})
      self.be.addData('step',    {'comment': 'This will take a long time.', 'name': 'Get spray machine'})
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
      print(self.be.outputHierarchy())

      ### TEST PROCEDURES
      print('\n*** TEST PROCEDURES ***')
      sopDir = self.dirName+os.sep+'StandardOperatingProcedures'
      os.makedirs(sopDir)
      with open(sopDir+os.sep+'Nanoindentation.org','w') as fOut:
        fOut.write('* Put sample in nanoindenter\n* Do indentation\nDo not forget to\n- calibrate tip\n- *calibrate stiffness*\n')
      with open(sopDir+os.sep+'SEM.md','w') as fOut:
        fOut.write('# Put sample in SEM\n# Do scanning\nDo not forget to\n- contact the pole-piece\n- **USE GLOVES**\n')
      self.be.addData('procedure', {'name': 'StandardOperatingProcedures'+os.sep+'SEM.md', 'comment': '#v1'})
      self.be.addData('procedure', {'name': 'StandardOperatingProcedures'+os.sep+'Nanoindentation.org', 'comment': '#v1'})
      print(self.be.output('Procedures'))

      ### TEST SAMPLES
      print('*** TEST SAMPLES ***')
      self.be.addData('sample',    {'name': 'AlFe cross-section', 'chemistry': 'Al99.9; FeMnCr ', 'qrCode': '13214124 99698708', 'comment': 'after OPS polishing'})
      print(self.be.output('Samples'))
      print(self.be.outputQR())

      ###  TEST MEASUREMENTS AND SCANNING/CURATION
      print('*** TEST MEASUREMENTS AND SCANNING/CURATION ***')
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/Zeiss.tif', semDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/RobinSteel0000LC.txt', indentDirName)
      shutil.copy(self.be.softwarePath+'/ExampleMeasurements/1500nmXX 5 7074 -4594.txt', indentDirName)
      self.be.scanTree()
      # TEST THAT LOCAL FILES/THUMBNAILS EXIST
      self.assertTrue(os.path.exists(semDirName+'Zeiss_tif_jamDB.jpg'),'Zeiss jamDB not created')
      self.assertTrue(os.path.exists(indentDirName+'1500nmXX 5 7074 -4594_txt_jamDB.svg'),'Micromaterials jamDB not created')
      self.assertTrue(os.path.exists(indentDirName+'RobinSteel0000LC_txt_jamDB.svg'),'Hysitron jamDB not created')

      ### USE GLOBAL FILES
      print('*** USE GLOBAL FILES ***')
      self.be.changeHierarchy(semStepID)
      self.be.addData('measurement', {'name': 'https://upload.wikimedia.org/wikipedia/commons/a/a4/Misc_pollen.jpg'})
      self.assertTrue(os.path.exists(semDirName+'Misc_pollen_jamDB.jpg'),'Wikipedia jamDB not created')


      ### VERIFY DATABASE INTEGRITY
      print("\n*** VERIFY DATABASE INTEGRITY ***")
      print(self.be.checkDB(verbose=True))

      ### CHANGE THOSE FILES
      print("\n*** TRY TO CHANGE THOSE FILES ***")
      cmd = ['convert',semDirName+'Zeiss.tif','-fill','white','+opaque','black',semDirName+'Zeiss.tif']
      try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
      except:
        print('** COULD NOT CHANGE IMAGE Zeiss.tif')


      ### ADD OWN DATATYPE
      print('\n*** ADD OWN DATATYPE ***')
      self.be.exit()
      print(self.be.softwarePath)

      # ***** enter new data-case: swimming
      # "swimming": {
      #     "config":["SwimmingExcercise"],
      #     "default":[
      #       {"name":"distance",   "long":"What distance did you swimm?",         "length":8},
      #       {"name":"stroke",     "long":"What stroke did you swim?",            "length":25},
      #       {"name":"pool",       "long":"What was the length of the pool?",     "length":5},
      #       {"name":"comment","long":"#tags comments :field:value:",             "length":50}
      #       ]
      # },

    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
      self.assertTrue(False,'Exception occurred')
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()