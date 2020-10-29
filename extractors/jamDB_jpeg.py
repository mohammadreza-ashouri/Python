"""create measurement data from random .jpeg file
"""
import logging, traceback
from io import BytesIO
import requests
from PIL import Image

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, ('png','jpg','svg'), dictionary of metadata
  """
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName).convert("L").convert("P")
    meta = {'measurementType':['unknown'],
            'metaVendor':{},
            'metaUser':{}}
    return image, 'jpg', meta
  except:
    logging.error("image_JPEG: JPEG "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
