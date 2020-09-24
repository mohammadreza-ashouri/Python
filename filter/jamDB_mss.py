"""create measurement data from .mss file

- MTS, Agilent, Keysight, KLA, NanomechanicsInc nanoindentation raw data
  proprietary binary files
"""

def getMeasurement(fileName, doc):
  """
  Args:
     fileName: full path file name
     doc: supplied to guide image creation doc['type']
  """
  return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
