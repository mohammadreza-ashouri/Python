"""extract data from .mss file
- MTS, Agilent, Keysight, KLA, NanomechanicsInc nanoindentation raw data
  proprietary binary files
"""

def use(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  #final return if nothing successful
  return None, ['', [], {}, {}]
