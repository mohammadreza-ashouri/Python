"""create measurement data from .mss file

- MTS, Agilent, Keysight, KLA, NanomechanicsInc nanoindentation raw data
  proprietary binary files
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
