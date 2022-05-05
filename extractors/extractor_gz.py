"""extract data from .hdf5 file
"""
import io, os, json
import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib
from PIL import Image, ImageChops

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if '-type' not in doc:
    doc['-type'] = []
  if fileName.endswith('.nii.gz'):
    img = nib.load(fileName)
    data = img.get_fdata()
    if doc['-type'][2:] == ['MRT_image', '3D']:#: plot 3D representation
      fig    = plt.figure()
      ax     = fig.gca(projection='3d')
      x      = np.arange(data.shape[0])
      y      = np.arange(data.shape[1])
      # levels=np.linspace(Z1.min(), Z1.max(), 100)
      z0 = int(data.shape[2]/4)
      z1 = int(data.shape[2]/2)
      z2 = int(data.shape[2]/4*3)
      t0 = int(data.shape[3]/2)
      X, Y   = np.meshgrid(x, y)
      ax.contourf(X, Y,data[:,:,z0,t0], zdir='z', offset=z0, cmap='gray_r', alpha=0.5)
      ax.contourf(X, Y,data[:,:,z1,t0], zdir='z', offset=z1, cmap='gray_r', alpha=0.5)
      ax.contourf(X, Y,data[:,:,z2,t0], zdir='z', offset=z2, cmap='gray_r', alpha=0.5)
      ax.set_xlim3d(0, data.shape[0])
      ax.set_ylim3d(0, data.shape[1])
      ax.set_zlim3d(0, data.shape[2])

      # x      = np.arange(data.shape[0])
      # y      = np.arange(data.shape[1])
      # z      = np.arange(data.shape[2])
      # x0 = int(data.shape[0]/2)
      # y0 = int(data.shape[1]/2)
      # z0 = int(data.shape[2]/2)
      # t0 = int(data.shape[3]/2)
      # levels=np.linspace(np.min(data), np.max(data), 10 )
      # print(levels)
      # # Z, Y   = np.meshgrid(z[:z0], y)
      # # ax.contourf(data[x0,:,:z0,t0], Y, Z, zdir='x', offset=x0, zorder=1)
      # X, Y   = np.meshgrid(x, y)
      # ax.contourf(X, Y,data[:,:,z0,t0], zdir='z', offset=z0, zorder=2)
      # Z, Y   = np.meshgrid(z[z0:], y)
      # ax.contourf(data[x0,:,z0:,t0], Y, Z, zdir='x', offset=x0, levels=levels)
      # # Z, X   = np.meshgrid(z, x)
      # # ax.contourf(X, data[:,y0,:,t0], Z, zdir='y', offset=y0)


    elif doc['-type'][2:] == ['MRT_image', 'inverted']:#: plot in color
      ax = plt.subplot(111)
      ax.imshow(data[:,:, int(data.shape[2]/2), int(data.shape[3]/2)], cmap='magma_r')

    else:                                             #default: default | plot gray scale
      ax = plt.subplot(111)
      ax.imshow(data[:,:, int(data.shape[2]/2), int(data.shape[3]/2)], cmap='gray')
      doc['-type'] += ['MRT_image']

    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight')
    buf.seek(0)
    im = Image.open(buf)
    #trim white space around picture
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -20)
    bbox = diff.getbbox()
    if bbox:
        im = im.crop(bbox)
    #metadata
    metaVendor = dict(img.header)
    if os.path.exists(fileName[:-7]+'.json'):
      metaVendor.update(json.loads(open(fileName[:-7]+'.json').read()))
    for key in metaVendor:
      metaVendor[key] = str(metaVendor[key])
    return im, ['jpg', doc['-type'], metaVendor,
      {'numSlices':data.shape[2], 'numTimesteps':data.shape[3], 'numMetaVendor':len(metaVendor) }]

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
