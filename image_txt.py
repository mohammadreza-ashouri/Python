import matplotlib.pyplot as plt
from nanoIndent import Indentation


def getImage(fileName):
  #if Hysitron file
  i = Indentation(fileName)
  i.updateSlopes()
  img = i.plot(False,False)
  return img, 'line', i.meta
