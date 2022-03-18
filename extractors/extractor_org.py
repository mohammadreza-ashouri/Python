"""extract data from Org-mode .org file
"""
import pypandoc

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if '-type' not in doc:
    doc['-type'] = []
  try:
    fIn = open(fileName,'r')
    text = pypandoc.convert_text(fIn.read(), 'md', format='org')
    return text, ['text', doc['-type']+['org-mode'], {}, {}]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
