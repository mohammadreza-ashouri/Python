"""create measurement data from .csv file
"""
from nanoTrib_surface import Surface

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaCustom]
  """
  # VK-X1000 Series
  try:
    with open(fileName,'r') as inFile:
      _     = inFile.readline()
      line2 = inFile.readline()
      line3 = inFile.readline()
      if line2 == '"Model";"VK-X1000 Series"\n' and line3 == '"Data type";"ImageDataCsv"\n':
        s = Surface(fileName)
        if s is None:
          raise ValueError
        s.createImage()
        return s.image, ['jpg', doc['type']+['surface'], s.meta, {}]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
