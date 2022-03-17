"""extract data from .ser file
"""
import os, struct, traceback
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from skimage import exposure
import ncempy.io as nio
from Tif import Tif

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content  [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  # my default
  if '-type' not in doc or len(doc['-type']) <= 3:
    doc['-type'] = ['measurement', 'TEM', 'ser_emd', 'threshold', 'adaptive']

  try:
    metaVendor = nio.read(fileName)
    #separate image and metadata
    image = metaVendor['data']
    del metaVendor['data']
    #copy all metadata in metaVendor into metaVendor-root
    if 'metadata' in metaVendor:
      metaVendor = {**metaVendor, **metaVendor['metadata']}
      del metaVendor['metadata']
    metaUser = {}

    i = Tif(None,'Void')
    if doc['-type'][2:] == ['ser_emd', 'no threshold', 'default']: #: no thresholding of intensity, no rescaling
      image = image/255.
    if doc['-type'][2:] == ['ser_emd', 'threshold', 'default']:   #: threshold intensity to 1024, no rescaling
      image = image['data']/4.
    if doc['-type'][2:] == ['ser_emd', 'no threshold', 'adaptive']: #: no thresholding of intensity, adaptive rescaling
      image = exposure.equalize_adapthist(image, clip_limit=0.01)*255
    if doc['-type'][2:] == ['ser_emd', 'threshold', 'adaptive']:   #: threshold intensity to 1024, adaptive rescaling
      image = np.array(image/4, dtype=np.uint8)
      image = exposure.equalize_adapthist(image, clip_limit=0.01)*255
    i.image = Image.fromarray(image.astype(np.uint8)).convert("L").convert("P")

    i.origImage = i.image.copy()
    i.pixelSize = metaVendor['pixelSize'][0]
    if 'pixelSizeUnit' in metaVendor and metaVendor['pixelSizeUnit'][0]=='nm':
      i.pixelSize /= 1000.
    elif 'pixelUnit' in metaVendor and metaVendor['pixelUnit'][0]=='m':
      i.pixelSize *= 1.e6
    else:
      print("**Error: Unknown pixelsize")
    i.widthPixel, i.heightPixel  = image.shape
    i.width, i.height = i.widthPixel*i.pixelSize, i.heightPixel*i.pixelSize

    i.addScaleBar()
    return i.image, ['jpg', doc['-type'], metaVendor, metaUser]

    # else:
    #   raise ValueError  #if header has wrong format

  except:
    print(traceback.format_exc())

  # other data routines follow here
  # ....

  #final return if nothing successful
  return None, ['', [], {}, {}]
