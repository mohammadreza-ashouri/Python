#!/usr/bin/python3
import js2py
from commonTools import commonTools as cT

import json, re
import base64, io
import js2py, os
from PIL import Image


def jsonValidator(data):
  """
  for debugging, test if valid json object

  Args: 
     data: string to test
  """
  try:
    json.loads(json.dumps(data) )
    return True
  except ValueError as error:
    print("**ERROR** invalid json: %s" % error)
    return False


def imageToString(url):
  """
  convert png file to b64-string

  future: test if jpeg and png strings are the same
  do I need to save jpeg, png as marker in list ['png',64byte]
  https://stackoverflow.com/questions/16065694/is-it-possible-to-create-encoded-base64-url-from-image-object

  Args:
     url: path to image
  """
  encoded = base64.b64encode(open(url,'rb').read())
  aString = encoded.decode()
  return aString


def stringToImage(aString, show=True):
  """
  convert a b64-string to png file

  Args:
     aString: 64byte string of image
     show: show image
  """
  imgdata = base64.b64decode(aString)
  image = Image.open(io.BytesIO(imgdata))
  if show:
    image.show()
  return image


def translateJS2PY():
  """ translate js-code to python
  """
  js2py.translate_file('../ReactJS/src/commonTools.js', 'commonTools.py')
  return

###########################################
##### MAIN FUNCTION
###########################################
if __name__=="__main__":
  translateJS2PY()
