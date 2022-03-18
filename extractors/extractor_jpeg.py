"""extract data from random .jpeg file: Wrapper for jpg
"""
from pasta_jpg import use as ex_use

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if '-type' not in doc:
    doc['-type'] = []

  return ex_use(fileName, doc)
