from Tif import Tif

def getImage(fileName):
  i = Tif(fileName)
  i.enhance()
  i.addScaleBar()
  imgType = "waves"
  meta = {'measurementType':"Zeiss tif image"}
  return i.image, imgType, meta
