import matplotlib.pyplot as plt
from nanoIndent import Indentation

def getImage(fileName):
  #if Hysitron file
  i = Indentation(fileName)
  i.nextTest()
  f, ax = plt.subplots()
  ax.plot(i.h,i.p)
  ax.set_xlim(left=0)
  ax.set_ylim(bottom=0)
  ax.set_xlabel('depth [um]')
  ax.set_ylabel('force [mN]')
  imgType = "line"
  meta = {'measurementType':"Hysitron Indentation"}
  return ax, imgType, meta
