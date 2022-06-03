#!/usr/bin/python3
"""TEST using the FULL set of python-requirements """
import os, shutil, traceback, logging, subprocess
import warnings, json
import unittest
from backend import Pasta

class TestStringMethods(unittest.TestCase):
  """
  derived class for this test
  """
  def __init__(self, *args, **kwargs):
    super(TestStringMethods, self).__init__(*args, **kwargs)
    self.be = None

  def test_main(self):
    """
    main function
    """
    # initialization: create database, destroy on filesystem and database and then create new one
    warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
    warnings.filterwarnings('ignore', message='invalid escape sequence')
    warnings.filterwarnings('ignore', category=ResourceWarning, module='PIL')
    warnings.filterwarnings('ignore', category=ImportWarning)
    warnings.filterwarnings('ignore', module='js2py')

    configName = 'pasta_tutorial'
    self.be = Pasta(configName, initViews=True, initConfig=False)

    try:
      ### ADD ONE MORE LEVEL
      print('\n*** ADD OWN DATATYPE ***')
      # Update ontology
      newOntology = self.be.db.db['-ontology-']
      newOntology['x3'] = [
                {'name': '-name',   'query': 'What is the name?', 'required':True},
                {'name': "comment","query":"#tags comments :field:value:"}
      ]
      newOntology.save()
      #restart
      self.be.exit()
      self.be = Pasta(configName, initViews=True, initConfig=False)
      self.assertTrue(list(self.be.hierarchyLabels)==['x0','x1','x2','x3'],'Level not added')
      print('\n*** DONE WITH VERIFY ***')

    except:
      print('ERROR OCCURRED IN VERIFY TESTING\n'+ traceback.format_exc() )
      raise
    return

  def tearDown(self):
    return

if __name__ == '__main__':
  unittest.main()
