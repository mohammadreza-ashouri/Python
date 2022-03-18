"""extract data from random .png file
"""
from io import BytesIO
import requests
from PIL import Image

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
  # plain png
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName)
    if 'Software' in image.info and 'matplotlib' in image.info['Software']:  #ignore python.matplotlib files since they are not measurements
      raise ValueError
    return image.convert('P'), ['jpg', doc['-type']+['image'], {}, {}]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
