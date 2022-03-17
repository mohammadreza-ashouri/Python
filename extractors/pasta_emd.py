"""extract data from .emd file: Wrapper for .ser
"""
from pasta_ser import use as ex_use

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content  [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  # my default
  if '-type' not in doc or len(doc['-type']) <= 3:
    doc['-type'] = ['measurement', 'TEM', 'ser_emd', 'no threshold', 'adaptive']

  return ex_use(fileName,doc)
