"""create measurement data from .csv file
"""
import logging, traceback

def getMeasurement(fileName, dataType):
  """
  Args:
     fileName: full path file name
     dataType: supplied to guide image creation dataType['type']
  """
  #pandas export (top-left cell is empty): do nothing
  with open(fileName,'r') as inFile:
    if inFile.readline().startswith(","):
      logging.info("Pandas output file "+fileName)
      return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}

  #other cases
  return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}