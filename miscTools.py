#!/usr/bin/python3
"""
Misc methods and diffinitions for json, colors
"""
import json, re, base64, io, os, stat
from hashlib import sha1
import numpy as np
from PIL import Image
import js2py

class bcolors:
  """
  Colors for Command-Line-Interface and output
  """
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


def createDirName(name,docType,thisChildNumber):
  """ create directory-name by using camelCase and a prefix

  Args:
      name: name with spaces etc.
      docType: document type used for prefix
      thisChildNumber: number of myself
  """
  from commonTools import commonTools as cT  #not globally imported since confuses translation
  if docType == 'project':
    return cT.camelCase(name)
  #steps, tasks
  if isinstance(thisChildNumber, str):
    thisChildNumber = int(thisChildNumber)
  return ('{:03d}'.format(thisChildNumber))+'_'+cT.camelCase(name)



def generic_hash(path):
  """
  Hash an object based on its mode.

  https://github.com/chris3torek/scripts/blob/master/githash.py

  Example implementation:
      result = generic_hash(sys.argv[1])
      print('%s: hash = %s' % (sys.argv[1], result))

  """
  if os.path.isdir(path):
    raise ValueError('This seems to be a directory '+fullpath)
  if os.path.islink(path):  #if link, dereference
    path = os.path.realpath(path)
  size = os.path.getsize(path)
  with open(path, 'rb') as stream:
    hasher = blob_hash(stream, size)
  shasum = hasher.hexdigest()
  # print("SHA CHECK",path,shasum,size)
  return shasum

def blob_hash(stream, size):
  """
  Return (as hash instance) the hash of a blob,
  as read from the given stream.
  """
  hasher = sha1()
  hasher.update(('blob %u\0' % size).encode('ascii'))
  nread = 0
  while True:
    # We read just 64K at a time to be kind to
    # runtime storage requirements.
    data = stream.read(65536)
    if data == b'':
      break
    nread += len(data)
    hasher.update(data)
  if nread != size:
    raise ValueError('%s: expected %u bytes, found %u bytes' % (stream.name, size, nread))
  return hasher



def jsonValidator(data):
  """
  for debugging, test if valid json object
  - not really used
   Args:
     data: string to test
  """
  try:
    json.loads(json.dumps(data))
    return True
  except ValueError as error:
    print("**ERROR** invalid json: %s" % error)
    return False


def imageToString(url):
  """
  *DEPRECATED*
  convert png file to b64-string
  - not really used

  future: test if jpeg and png strings are the same
  do I need to save jpeg, png as marker in list ['png',64byte]
  https://stackoverflow.com/questions/16065694/is-it-possible-to-create-encoded-base64-url-from-image-object

  Args:
      url: path to image
  """
  encoded = base64.b64encode(open(url, 'rb').read())
  aString = encoded.decode()
  return aString


def stringToImage(aString, show=True):
  """
  *DEPRECATED*
  convert a b64-string to png file
  - not really used

  Args:
    aString: 64byte string of image
    show: show image
  """
  imgdata = base64.b64decode(aString)
  image = Image.open(io.BytesIO(imgdata))
  if show:
    image.show()
  return image


def createQRcodeSheet(fileName="../qrCodes.pdf"):
  """
  Documentation QR-codes
  - img = qrcode.make("testString",error_correction=qrcode.constants.ERROR_CORRECT_M)
  - or ERROR-CORRECT_H for better errorcorrection
  Sizes:
  - QR code size 1.5-2cm
  - with frame 2.25-3cm
  - Page size 18x27cm; 6x9 = 54
  """
  import qrcode
  from commonTools import commonTools as cT  # don't import globally since it disturbs translation
  img = qrcode.make(cT.uuidv4(),
                    error_correction=qrcode.constants.ERROR_CORRECT_M)
  size = img.size[0]
  hSize = 6*size
  vSize = 9*size
  new_im = Image.new('RGB', (hSize, vSize))
  for i in np.arange(0, hSize, size):
    for j in np.arange(0, vSize, size):
      img = qrcode.make(cT.uuidv4(),
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
      # if j==0:  #make top row yellow
      #   data = np.array(img.convert("RGB"))
      #   red, green, blue = data.T
      #   mask = (red==255) & (green==255) & (blue==255)
      #   data[:,:,:][mask.T]=(255,255,0)
      #   img = Image.fromarray(data)
      new_im.paste(img, (i, j))
  new_im.save(fileName)
  return


def translateJS2PY():
  """
  Translate js-code to python-code using js2py lib
  - remove the last export-lines from commonTools.js
  """
  jsString = open('./commonTools.js', "r").read()
  jsString = re.sub(r"export.+;", "", jsString)
  jsFile = io.StringIO(jsString)
  js2py.translate_file(jsFile, 'commonTools.py')
  print('translated js->py')
  return



###########################################
##### MAIN FUNCTION
###########################################
if __name__ == "__main__":
  # translate js-code to python
  translateJS2PY()
  # prepare new sheet with QR-codes, does not hurt to create new
  createQRcodeSheet()
