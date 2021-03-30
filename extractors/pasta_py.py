"""create measurement data from .py file
- python file
"""

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaCustom]
  """
  #final return if nothing successful
  return None, ['', [], {}, {}]
