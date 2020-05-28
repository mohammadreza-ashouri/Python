"""create measurement data from random .jpeg file
"""
from PIL import Image
import requests
from io import BytesIO
import logging, traceback

def getImage(fileName, dataType):
  """
  Args:
     fileName: full path file name
     dataType: supplied to guide image creation dataType['type']
  """
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName).convert("L").convert("P")
    meta = {'measurementType':['unknown'],
            'metaSystem':{},
            'metaUser':{}}
    return image, 'waves', meta
  except:
    logging.error("image_JPEG: JPEG "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaSystem':{},'metaUser':{}}