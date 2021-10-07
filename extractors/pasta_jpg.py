"""create measurement data from random .jpeg file
"""
from io import BytesIO
import requests
from PIL import Image

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaUser]
  """
  # plain jpeg
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName).convert("L").convert("P")
    return image, ['jpg', doc['type']+['image'], {}, {}]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
