#!/usr/bin/python3
import os, shutil, traceback, logging, subprocess
import warnings, json
import unittest
from datetime import datetime
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
    self.be = Pasta(configName, initViews=True, initConfig=False)

    try:
      ### ADD MORE DATA
      self.be.addData('instrument', {'name': 'G200X', 'vendor':'KLA', 'model':'KLA G200X'})
      self.be.addData('instrument', {'name': 'B1', 'vendor':'Synthon', 'model':'Berkovich tip'})
      output = self.be.output('instrument',True)
      idKLA, idSynthon = None, None
      for line in output.split('\n'):
        if 'KLA' in line:
          idKLA = line.split('|')[-1].strip()
        if 'Synthon'  in line:
          idSynthon = line.split('|')[-1].strip()
      self.be.db.addAttachment(idKLA, "Right side of instrument",
        {'date':datetime.now().isoformat(),'remark':'Worked well','docID':idSynthon,'user':'nobody'})
      self.be.db.addAttachment(idKLA, "Right side of instrument",
        {'date':datetime.now().isoformat(),'remark':'Service','docID':'','user':'nobody'})
      print('\n*** DONE WITH VERIFY ***')

    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
      self.assertTrue(False,'Exception occurred')
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()
