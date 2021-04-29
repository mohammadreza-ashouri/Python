"""create measurement data from .tif file
"""
from Tif import Tif

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaCustom]
  """
  # my default
  if len(doc['type']) <= 3:
    doc['type'] = ['measurement', 'tif', 'image', 'scale', 'rescale']

  # try Steffen's Tif library
  try:
    i = Tif(fileName)
    if i is None:
      raise ValueError
    if doc['type'][2:] == ['image', 'no_scale', 'adaptive']: #: plot with no scale bar, adaptive grayscales and crop bottom white databar
      i.autoCrop()
      i.enhance("adaptive")
      return i.image, ['jpg', doc['type'], i.meta, {}]

    if doc['type'][2:] == ['image', 'scale', 'adaptive']:   #: plot with scale bar, adaptive grayscales and crop bottom white databar
      i.autoCrop()
      i.enhance("adaptive")
      i.addScaleBar()
      return i.image, ['jpg', doc['type'], i.meta, {}]

    if doc['type'][2:] == ['image', 'no_scale', 'rescale']: #: plot with no scale bar, rescale grayscales and crop bottom white databar
      i.autoCrop()
      i.enhance()
      return i.image, ['jpg', doc['type'], i.meta, {}]

    if doc['type'][2:] == ['image', 'scale', 'rescale']:    #: plot with scale bar, rescale grayscales and crop bottom white databar
      i.autoCrop()
      i.enhance()
      i.addScaleBar()
      return i.image, ['jpg', doc['type'], i.meta, {}]

    if doc['type'][2:] == ['image', 'default']:             #: default image, no change
      return i.image, ['jpg', doc['type']+['image'], i.meta, {}]

    else:
      raise ValueError

  except:
    pass

  # other data routines follow here
  # ....

  #final return if nothing successful
  return None, ['', [], {}, {}]
