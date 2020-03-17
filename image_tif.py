from Tif import Tif


def getImage(fileName):
  i = Tif(fileName)
  i.enhance()
  i.addScaleBar()
  return i.image, 'waves', i.meta
