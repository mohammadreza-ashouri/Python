#!/usr/bin/python3
"""
Misc methods and diffinitions for json, colors
"""

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
      name (string): name with spaces etc.
      docType (string): document type used for prefix
      thisChildNumber (int): number of myself

  Returns:
    string: directory name with leading number
  """
  from commonTools import commonTools as cT  #not globally imported since confuses translation
  if docType == 'x0':
    return cT.camelCase(name)
  #steps, tasks
  if isinstance(thisChildNumber, str):
    thisChildNumber = int(thisChildNumber)
  return ('{:03d}'.format(thisChildNumber))+'_'+cT.camelCase(name)



def generic_hash(path, forceFile=False):
  """
  Hash an object based on its mode.

  inspired by:
  https://github.com/chris3torek/scripts/blob/master/githash.py

  Example implementation:
      result = generic_hash(sys.argv[1])
      print('%s: hash = %s' % (sys.argv[1], result))

  Args:
    path (string): path
    forceFile (bool): force to get shasum of file and not of link (False for gitshasum)

  Returns:
    string: shasum

  Raises:
    ValueError: shasum of directory not supported
  """
  import os
  from urllib import request
  if os.path.isdir(path):
    raise ValueError('This seems to be a directory '+path)
  if forceFile:
    path = os.path.realpath(path)
  if os.path.islink(path):    #if link, hash the link
    shasum = symlink_hash(path)
  elif os.path.isfile(path):  #Local file
    size = os.path.getsize(path)
    with open(path, 'rb') as stream:
      shasum = blob_hash(stream, size)
  else:                     #Remote file
    site = request.urlopen(path)
    meta = site.headers
    size = int(meta.get_all('Content-Length')[0])
    shasum = blob_hash(site, size)
  return shasum


def upOut(key):
  """
  key (bool): key
  """
  import keyring as cred
  key = cred.get_password('pastaDB',key)
  if key is None:
    key = ':'
  else:
    key = ':'.join(key.split('bcA:Maw'))
  return key

def upIn(key):
  """
  key (bool): key
  """
  import keyring as cred
  from commonTools import commonTools as cT  # don't import globally since it disturbs translation
  key = 'bcA:Maw'.join(key.split(':'))
  id_  = cT.uuidv4()
  cred.set_password('pastaDB',id_,key)
  return id_


def symlink_hash(path):
  """
  Return (as hash instance) the hash of a symlink.
  Caller must use hexdigest() or digest() as needed on
  the result.

  Args:
    path (string): path to symlink

  Returns:
    string: shasum of link, aka short string
  """
  import os
  from hashlib import sha1
  hasher = sha1()
  data = os.readlink(path).encode('utf8', 'surrogateescape')
  hasher.update(('blob %u\0' % len(data)).encode('ascii'))
  hasher.update(data)
  return hasher.hexdigest()


def blob_hash(stream, size):
  """
  Return (as hash instance) the hash of a blob,
  as read from the given stream.

  Args:
    stream (string): content to be hashed
    size (int): size of the content

  Returns:
    string: shasum

  Raises:
    ValueError: size given is not the size of the stream
  """
  from hashlib import sha1
  hasher = sha1()
  hasher.update(('blob %u\0' % size).encode('ascii'))
  nread = 0
  while True:
    data = stream.read(65536)     # read 64K at a time for storage requirements
    if data == b'':
      break
    nread += len(data)
    hasher.update(data)
  if nread != size:
    raise ValueError('%s: expected %u bytes, found %u bytes' % (stream.name, size, nread))
  return hasher.hexdigest()


def imageToString(url):
  """
  *DEPRECATED*
  convert png file to b64-string
  - not really used

  future: test if jpeg and png strings are the same
  do I need to save jpeg, png as marker in list ['png',64byte]
  https://stackoverflow.com/questions/16065694/is-it-possible-to-create-encoded-base64-url-from-image-object

  Args:
      url (string): path to image

  Returns:
    string: image as string
  """
  import base64
  encoded = base64.b64encode(open(url, 'rb').read())
  aString = encoded.decode()
  return aString


def stringToImage(aString, show=True):
  """
  *DEPRECATED*
  convert a b64-string to png file
  - not really used

  Args:
    aString (string): 64byte string of image
    show (bool): show image

  Returns:
    Image: image of string
  """
  import base64, io
  from PIL import Image
  imgdata = base64.b64decode(aString)
  image = Image.open(io.BytesIO(imgdata))
  if show:
    image.show()
  return image


def getExtractorConfig(directory):
  """
  Rules:
  - each data-type in its own try-except
  - inside try: raise ValueError exception on failure/None
  - except empty: pass
  - all descriptions in type have to be small letters
  - if want to force to skip top datatypes and use one at bottom: if doctype... -> exception

  Args:
    directory (string): relative directory to scan

  Returns:
    list: list of [doctype-list, description]
  """
  import os
  configuration = {}
  for fileName in os.listdir(directory):
    if fileName.endswith('.py') and fileName!='scanExtractors.py':
      #start with file
      with open(directory+os.sep+fileName,'r') as fIn:
        lines = fIn.readlines()
        extractors = []
        baseType = ['measurement', fileName[6:-3]]
        ifInFile, headerState, header = False, True, []
        for idx,line in enumerate(lines):
          line = line.rstrip()
          if idx>0 and '"""' in line:
            headerState = False
          if headerState:
            line = line.replace('"""','')
            header.append(line)
            continue
          if "if doc['-type'][2:] == [" in line and "#:" in line:
            specialType = line.split('== [')[1].split(']:')[0]
            specialType = [i.strip()[1:-1] for i in specialType.split(',')]
            extractors.append([ baseType+specialType, line.split('#:')[1].strip() ])
            ifInFile = True
          elif "else:" in line and "#default:" in line:
            extractors.append([ baseType+[specialType[0]], line.split('#default:')[1].strip() ])
          elif "return" in line and not ifInFile:
            try:
              specialType = line.split("+['")[1].split("']")[0]
              extractors.append([ baseType+[specialType], '' ])
            except:
              pass
        configuration[fileName] = {'plots':extractors, 'header':'\n'.join(header)}
  return configuration


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
  import numpy as np
  from PIL import Image
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


def printQRcodeSticker(codes={},
                       page={'size':[991,306], 'tiles':2, 'margin': 60, 'font':40},
                       printer={'model':'QL-700', 'dev':'0x04f9:0x2042/3', 'size':'29x90'}):
  """
  Codes: key-value pairs of qr-code and label
   - filled to achieve tiles

  Sticker:
   - size: 90.3x29 mm => [991,306] px
   - tiles: number of items on the sticker
   - margin: margin between tiles
   - font: font size in px

  Printer:
   - model: brother label printer QL-700
   - dev: device in idVendor:idProduct/iSerial
     execute 'lsusb -v'; find printer
   - size: label size in mm
  """
  import qrcode, tempfile, os
  import numpy as np
  from PIL import Image, ImageDraw, ImageFont
  from commonTools import commonTools as cT  # don't import globally since it disturbs translation
  fnt = ImageFont.truetype("arial.ttf", page['font'])
  offset    = int((page['size'][0]+page['margin'])/page['tiles'])
  qrCodeSize= min(offset-page['font']-page['margin'], page['size'][1])
  print("Effective label size",page['size'], "offset",offset, 'qrCodeSize',qrCodeSize)
  cropQRCode  = 40         #created by qrcode library
  numCodes = 0
  image = Image.new('RGBA', page['size'], color=(255,255,255,255) )
  for idx in range(page['tiles']):
    if idx<len(codes):
      codeI, text = codes[idx]
    else:
      codeI, text =  '', ''
    if len(codeI)==0:
      codeI = cT.uuidv4()
    # add text
    width, height = fnt.getsize(text)
    txtImage = Image.new('L', (width, height), color=255)
    d = ImageDraw.Draw(txtImage)
    d.text( (0, 0), text,  font=fnt, fill=0)
    txtImage=txtImage.rotate(90, expand=1)
    if width>page['size'][1]:  #shorten it to fit into height
      txtImage=txtImage.crop((0,width-page['size'][1],height,width))
    image.paste(txtImage, (numCodes*offset+qrCodeSize-4, int((page['size'][1]-txtImage.size[1])/2)   ))
    # add qrcode
    qrCode = qrcode.make(codeI, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qrCode = qrCode.crop((cropQRCode, cropQRCode, qrCode.size[0]-cropQRCode, qrCode.size[0]-cropQRCode))
    qrCode = qrCode.resize((qrCodeSize, qrCodeSize))
    image.paste(qrCode, (numCodes*offset, int((page['size'][1]-qrCodeSize)/2)))
    numCodes += 1
  tmpFileName = tempfile.gettempdir()+os.sep+'tmpQRcode.png'
  print('Create temp-file',tmpFileName)
  image.save(tmpFileName)
  cmd = 'brother_ql -b pyusb -m '+printer['model']+' -p usb://'+printer['dev']+' print -l '+printer['size']+' -r auto '+tmpFileName
  reply = os.system(cmd)
  if reply>0:
    print('**ERROR mpq01: Printing error')
    image.show()
  return



def checkConfiguration(repair=False):
  """
    Check configuration file .pasta.json for consistencies

  Args:
      repair (bool): repair configuration

  Returns:
      string: output incl. \n
  """
  import os, json
  from cloudant.client import CouchDB
  try:
    fConf = open(os.path.expanduser('~')+'/.pasta.json','r')
  except:
    return 'Verify configuration\n**ERROR mcc00: config file does not exist.\nFAILURE\n'
  conf = json.load(fConf)
  output = ''
  #test static entries
  if not '-softwareDir' in conf:
    output += '**ERROR mcc01a: No -softwareDir in config file\n'
    if repair:
      conf['-softwareDir'] = os.path.dirname(os.path.abspath(__file__))
  if not '-userID' in conf:
    output += '**ERROR mcc01b: No -userID in config file\n'
    if repair:
      conf['-userID'] = os.getlogin()
  if not '-eargs' in conf:
    output += '**ERROR mcc01c: No -eargs in config file\n'
    if repair:
      conf['-eargs'] = {"editor":"", "ext":"", "style":""}
  if not '-magicTags' in conf:
    output += '**ERROR mcc01d: No -magicTags in config file\n'
    if repair:
      conf['-magicTags'] = []
  if not '-qrPrinter' in conf:
    output += '**ERROR mcc01e: No -qrPrinter in config file\n'
    if repair:
      conf['-qrPrinter'] = []
  if not '-tableFormat-' in conf:
    output += '**ERROR mcc01f: No -tableFormat- in config file\n'
    if repair:
      conf['-tableFormat-'] = {}
  if not '-extractors-' in conf:
    output += '**ERROR mcc01g: No -extractors- in config file\n'
    if repair:
      conf['-extractors-'] = {}
  if not "-defaultLocal" in conf:
    output += '**ERROR mcc01h: No -defaultLocal in config file\n'
    if repair:
      conf['-defaultLocal'] = [i for i in conf.keys() if i[0]!='-' and 'path' in conf[i]][0]
  else:
    if not conf['-defaultLocal'] in conf:
      output += '**ERROR mcc01i: -defaultLocal entry '+conf['-defaultLocal']+' not in config file\n'
      if repair:
        conf['-defaultLocal'] = [i for i in conf.keys() if i[0]!='-' and 'path' in conf[i]][0]

  # go through all connection entries
  for key in conf:
    if key[0]=='-':
      continue
    if not 'database' in conf[key]:
      output += '**ERROR mcc02a: No database in config |'+key+'\n'
    if not 'cred' in conf[key]:
      output += '**ERROR mcc03: No user-credentials (username,password) in config |'+key+'\n'
    elif 'path' in conf[key]:
      u,p = upOut(conf[key]['cred']).split(':')
      client = CouchDB(u, p, url='http://127.0.0.1:5984', connect=True)
      if not conf[key]['database'] in client.all_dbs():
        output += '**ERROR mcc04: Database not on local server configuration |'+key+'\n'
    if 'url' in conf[key]:
      # remote entry
      continue
    # local entry
    if 'path' in conf[key]:
      if not os.path.exists(conf[key]['path']):
        output += '**ERROR mcc05: Path does not exist |'+str(conf[key]['path'])+'\n'
    else:
      output += '**ERROR mcc02b: No path in config |'+key+'\n'
  #end
  if repair:
    with open(os.path.expanduser('~')+'/.pasta.json','w') as f:
      f.write(json.dumps(conf,indent=2))
  if output=='':
    output='Verify configuration\nSUCCESS\n'
  else:
    output='Verify configuration\n'+output+'FAILURE\n'
  return output


def translateJS2PY():
  """
  Translate js-code to python-code using js2py lib
  - remove the last export-lines from commonTools.js
  """
  import re, io
  import js2py
  jsString = open('./commonTools.js', "r").read()
  jsString = re.sub(r"export.+;", "", jsString)
  jsFile = io.StringIO(jsString)
  js2py.translate_file(jsFile, 'commonTools.py')
  print('..success: translated commonTools.js->commonTools.py')
  return


def errorCodes(verbose=False):
  """
  go through all source files and list error codes

  Args:
     verbose (bool): print information about printing statements
  """
  import os, re, json
  ignoreFiles = ['checkAllVersions.py','pastaCLI.py','commonTools.py']
  knownErrcodes = {
    "mcc01":"Use automatic configuration repair",
    "mcc02":"Repair with configuration-editor",
    "mcc03":"Repair with configuration-editor and restart",
    "mcc04":"Restart using this database",
    "mcc05":"Please create path manually",
    "dit01":"Likely userName / password not correct"
  }
  output = 'automatically created MD file of error codes by miscTools:errorCodesp\n'
  if verbose:
    print('All terminal output')
  for fileName in os.listdir('.'):
    if not fileName.endswith('.py') or fileName in ignoreFiles:
      continue
    content = open(fileName,'r').read().split('\n')
    errors = [' '+i.split('**ERROR')[1] for i in content if '**ERROR' in i and 'if' not in i]   #SKIP ME ErrorCode
    errors = [i for i in errors if '#SKIP ME ErrorCode' not in i]
    errors = [i.replace(")","").replace("\\n'",'').replace("+f'{bcolors.ENDC}","").replace(",'","") for i in errors]
    errorsNew = []
    for err in errors:
      result = re.match(r"^[\w]{3}[\d]{2}\w*:",err.strip())
      if result:
        errCode = result.group()[:-1]
        err = '  - '+errCode+':'+err.strip()[result.end():]
        if errCode[:5] in knownErrcodes:
          err += '\n    '+knownErrcodes[errCode[:5]]
      errorsNew.append(err)
    if len(errorsNew)>0:
      output+='# '+fileName+'\n'+'\n'.join(errorsNew)+'\n\n'
    prints = [i.strip() for i in content if i.strip().startswith('print') and "**ERROR" not in i]  #SKIP ME ErrorCode
    if verbose:
      print('\n\n'+fileName+'\n  '+'\n  '.join(prints))
  fOut = open('../Documents/errorCodes.md','w')
  fOut.write(output)
  fOut = open('../ReactElectron/app/renderer/errorCodes.js','w')
  fOut.write('export const errorCodes =\n')
  json.dump(knownErrcodes,fOut)
  fOut.write(';')
  print('..success: assembled error-codes')
  return


###########################################
##### MAIN FUNCTION
###########################################
if __name__ == "__main__":
  translateJS2PY()    # translate js-code to python
  errorCodes()        # create overview of errorCodes
