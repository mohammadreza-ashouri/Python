#!/usr/bin/python3
import base64, os, sys, importlib
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#test if usage clear
if len(sys.argv)==1 or sys.argv[1]=='help':
  print("Usage:\n  testExtractor.py  path/to/file.png plotType\nWhere plotType is optional")
  sys.exit()
filePath = sys.argv[1]
plotType = sys.argv[2] if len(sys.argv)>2 else None
print('Test file',filePath)
print('Plot type',plotType)

#load corresponding file
extension = os.path.splitext(filePath)[1][1:]
pyFile = 'extractor_'+extension+'.py'
if os.path.exists(pyFile):
  module  = importlib.import_module(pyFile[:-3])
  content = module.use(filePath, {'type':plotType})
  #verify image
  if 'image' not in content:
    print('**Error: image not produced by extractor')
    sys.exit()
  if isinstance(content['image'],Image.Image):
    content['image'].show()
    print('**Warning: image is a PIL image: not a base64 string')
    print('Encode image via the following: pay attention to jpg/png which is encoded twice\n```')
    print('from io import BytesIO')
    print('figfile = BytesIO()')
    print('image.save(figfile, format="PNG")')
    print('imageData = base64.b64encode(figfile.getvalue()).decode()')
    print('image = "data:image/jpg;base64," + imageData')
    print('```')
  #verify image visually
  if isinstance(content['image'], str):
    extension = content['image'][11:14]
    i = base64.b64decode(content['image'][22:])
    i = BytesIO(i)
    i = Image.open(i)
    i.show()




#pastaELN.py extractorTest -p sub.nii.gz -c 'measurement/gz/MRT_image/3D'