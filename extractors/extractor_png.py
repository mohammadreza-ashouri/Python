"""extract data from a .png file
"""
import base64
from io import BytesIO
from PIL import Image
import numpy as np

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if 'type' not in doc or doc['type'] is None:
    doc['type'] = []
  # plain png
  try:
    image = Image.open(fileName)
    metaVendor = image.info
    maskBlackPixel = np.array(image)[:,:,0]<128
    metaUser   = {'number black pixel', len(maskBlackPixel[maskBlackPixel]),
                  'number all pixel', np.prod(image.size)}

    image = image.convert('P')
    figfile = BytesIO()
    image.save(figfile, format="PNG")
    imageData = base64.b64encode(figfile.getvalue()).decode()
    image = "data:image/png;base64," + imageData
    return {'image':image, 'type':doc['type']+['image'],\
            'metaVendor':metaVendor, 'metaUser':metaUser}
  except:  #embed into try: except if multiple possibilities; makes debugging harder since there tracestack
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return {}
