"""create measurement data from .csv file
"""
import logging

def getMeasurement(fileName, doc):
  """
  Args:
     fileName: full path file name
     doc: supplied to guide image creation doc['type']
  """
  #pandas export (top-left cell is empty): do nothing
  with open(fileName,'r') as inFile:
    if inFile.readline().startswith(","):
      logging.info("Pandas output file "+fileName+" Do nothing.")
      return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}

  #other cases
  return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
