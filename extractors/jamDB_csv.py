"""create measurement data from .csv file
"""
import logging
from nanoTrib_surface import Surface

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, ('png','jpg','svg'), dictionary of metadata
  """
  #pandas export (top-left cell is empty): do nothing
  with open(fileName,'r') as inFile:
    line1 = inFile.readline()
    line2 = inFile.readline()
    line3 = inFile.readline()
    if line1.startswith(","):
      logging.info("Pandas output file "+fileName+" Do nothing.")
      return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
    if line2 == '"Model";"VK-X1000 Series"\n' and line3 == '"Data type";"ImageDataCsv"\n':
      s = Surface(fileName)
      if s is not None:
        s.createImage()
        measurementType = [s.meta.pop('measurementType')] + doc['type'][2:]
        meta = {'measurementType':measurementType,
                'metaVendor':s.meta,
                'metaUser':{}}
        return s.image, 'jpg', meta

  #other cases
  return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
