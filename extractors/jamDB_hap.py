"""create measurement data from .hap file

- Fischer-Scope .hap file: unknown
"""

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, ('png','jpg','svg'), dictionary of metadata
  """
  return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}