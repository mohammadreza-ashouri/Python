"""create measurement data from random .png file
"""
from PIL import Image
import requests
from io import BytesIO
import logging, traceback

def getMeasurement(fileName, doc):
  """
  Args:
     fileName: full path file name
     doc: supplied to guide image creation doc['type']
  """
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName)
    if 'Software' in image.info and 'matplotlib' in image.info['Software']:  #ignore python.matplotlib files since they are not measurements
      return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
    else:
      image = image.convert("P")
      meta = {'measurementType':['unknown'],
              'metaVendor':{},
              'metaUser':{}}
    return image, 'png', meta
  except:
    logging.error("image_PNG: PNG "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}