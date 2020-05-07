"""create measurement data from random .jpeg file
"""
from PIL import Image
import requests
from io import BytesIO
import logging, traceback


def getImage(fileName, metaData):
  """
  Args:
     fileName: full path file name
     metaData: can be supplied to guide image creation metaData['measurementType'],metaData['plotType']
  """
  try:
    if "://" in fileName:
      response = requests.get(fileName)
      image = Image.open(BytesIO(response.content))
    else:
      image = Image.open(fileName).convert("L").convert("P")
    meta  = {'measurementType':'random'}
    return image, 'waves', meta
  except:
    logging.error("image_JPEG: JPEG "+fileName)
    logging.error(traceback.format_exc())
    return None, None, None