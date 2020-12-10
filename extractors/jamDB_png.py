"""create measurement data from random .png file
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
      image = Image.open(fileName)
    if 'Software' in image.info and 'matplotlib' in image.info['Software']:  #ignore python.matplotlib files since they are not measurements
      return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
    image = image.convert("P")
    meta = {'measurementType':['unknown'],
            'metaVendor':{},
            'metaUser':{}}
    return image, 'png', meta
  except:
    logging.error('extractor png: '+fileName+' not a measurement')
    #logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
