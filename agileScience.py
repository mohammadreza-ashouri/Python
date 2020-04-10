""" Python Backend
"""
import os, json, base64, hashlib, shutil
import importlib
import numpy as np
import matplotlib.pyplot as plt
import logging
from io import StringIO, BytesIO
from pprint import pprint
from asTools import imageToString, stringToImage
from asCloudant import Database
from commonTools import commonTools as cT


class AgileScience:
  """
  PYTHON BACKEND
  """

  def __init__(self, databaseName=None):
    """
    open server and define database

    Args:
        databaseName: name of database, otherwise taken from config file
    """
    # open configuration file and define database
    logging.basicConfig(filename='jams.log', filemode='w', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info("\nSTART JAMS")
    jsonFile = open(os.path.expanduser('~')+'/.agileScience.json')
    configuration = json.load(jsonFile)
    user         = configuration["user"]
    password     = configuration["password"]
    if databaseName is None:
        databaseName = configuration["database"]
    else:  # if test
        configuration['baseFolder'] = databaseName
    self.db = Database(user, password, databaseName)
    self.userID   = configuration["userID"]
    self.remoteDB = configuration["remote"]
    self.eargs   = configuration["eargs"]
    # open basePath (root of directory tree) as current working directory
    # self.cwd is the addition to basePath
    self.softwarePath = os.path.abspath(os.getcwd())
    self.basePath     = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    self.cwd          = ""
    if not self.basePath.endswith("/"):
        self.basePath += "/"
    if os.path.exists(self.basePath):
        os.chdir(self.basePath)
    else:
        logging.warning("Base folder did not exist. No directory saving\n"+self.basePath)
        self.cwd   = None
    # hierarchy structure
    self.dataDictionary = self.db.getDoc("-dataDictionary-")
    self.hierList = self.dataDictionary["-hierarchy-"]
    self.hierStack = []
    self.currentID  = None
    self.alive     = True
    return


  def exit(self, deleteDB=False):
    """
    Shutting down things

    Args:
      deleteDB: remove database
    """
    os.chdir(self.softwarePath)  #where program started
    self.db.exit(deleteDB)
    self.alive     = False
    logging.debug("\nEND JAMS")
    logging.shutdown()
    return


  ######################################################
  ### Change in database
  ######################################################
  def addData(self, docType, data, hierStack=[]):
    """
    Save data to data base, also after edit

    Args:
        docType: docType to be stored
        data: to be stored
        hierStack: hierStack from external functions
    """
    logging.info('jams.addData Got data: '+docType+' | '+str(hierStack))
    data['user']   = self.userID
    data['client'] = 'python version 0.1'
    if len(hierStack) == 0:
      hierStack = list(self.hierStack)
    # collect data and prepare
    if docType != '-edit-':
      #new document
      data['type'] = docType
      newDoc       = True
      if docType in self.hierList and docType!='project':
        #should not have childnumber in other cases for debugging
        thisStack = ' '.join(self.hierStack)
        view = self.db.getView('viewHierarchy/viewHierarchy', key=self.hierStack[0]) #not faster with cT.getChildren
        thisChildNumber = 0
        for item in view:
          if item['value'][2]=='project': continue
          if item['value'][0] == thisStack:
            thisChildNumber += 1
        data['childNum'] = thisChildNumber
      if docType in self.hierList:
        prefix = 't'
      else:
        prefix = docType[0]
      # find path name on local file system; name can be anything
      if self.cwd is not None:
        if docType in self.hierList:
          #project, step, task
          if docType=='project': thisChildNumber = -1
          data['path'] = self.createDirName(data['name'],data['type'],thisChildNumber)
        else:
          #measurement, sample, procedure
          if '://' in data['name']:                                 #make up name
            data['path'] = self.cwd + cT.camelCase( os.path.basename(data['name']))
            data.update( self.getImage(data['name']) )
          elif os.path.exists(self.basePath+data['name']):          #file exists
            data['path'] = data['name']
            data.update( self.getImage(data['path']) )
            data['name'] = os.path.basename(data['name'])
          elif os.path.exists(self.basePath+self.cwd+data['name']): #file exists
            data['path'] = self.cwd+data['name']
            data.update( self.getImage(data['path']) )
          else:                                                     #make up name
            data['path'] = self.cwd + cT.camelCase( os.path.basename(data['name']))
      ## add data to database
      data = cT.fillDocBeforeCreate(data, docType, hierStack, prefix).to_dict()
      data = self.db.saveDoc(data)
    else:
      #update document
      data = cT.fillDocBeforeCreate(data, '--', hierStack[:-1], '--').to_dict()
      data = self.db.updateDoc(data,self.hierStack[-1])
    ## adoptation of directory tree, information on disk
    if self.cwd is not None:
      if data['type'] in self.hierList:
        #project, step, task
        os.makedirs(self.basePath+data['path'], exist_ok=True)
        with open(self.basePath+data['path']+'/id_jams.json','w') as f:  #local path
          f.write(json.dumps(data))
      else:
        #measurement, sample, procedure
        with open(self.basePath+data['path'].replace('.','_'),'w') as f:
          f.write(json.dumps(data))
    self.currentID = data['_id']
    # reduce information before logging
    if 'image' in data: del data['image']
    if 'meta'  in data: data['meta']='length='+str(len(data['meta']))
    logging.debug("Data saved "+str(data))
    return


  def createDirName(self,name,docType,thisChildNumber):
    """ create directory-name by using camelCase and a prefix

    Args:
       name: name with spaces etc.
       docType: document type used for prefix
       thisChildNumber: number of myself
    """
    if 'project' in docType:
      return cT.camelCase(name)
    else:  #steps, tasks
      if isinstance(thisChildNumber, str):
        thisChildNumber = int(thisChildNumber)
      return ("{:03d}".format(thisChildNumber))+'_'+cT.camelCase(name)



  ######################################################
  ### Get data from database
  ######################################################
  def getDoc(self, id):
    """
    Wrapper for getting data from database

    Args:
        id: document id
    """
    return self.db.getDoc(id)


  def changeHierarchy(self, id):
    """
    Change through text hierarchy structure

    Args:
        id: information on how to change
    """
    if id is None or id in self.hierList:  # "project", "step", "task" are given: close
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-2])+'/'
    else:  # existing project ID is given: open that
      self.hierStack.append(id)
      if self.cwd is not None:
        path = self.db.getDoc(id)['path']
        dirName = path.split('/')[-1]
        os.chdir(dirName)
        self.cwd += dirName+'/'
    return

  def scanTree(self):
    """ Set up everything and starting from this document (project, step, ...) call scanDirectory
    - branch refers to things in database
    - directories refers to things on harddisk
    """
    projectBranch = self.outputHierarchy(onlyHierarchy=False, addID=True)
    thisBranch = self.getSubBranch(projectBranch.split("\n"),self.hierStack[-1])
    self.scanDirectory(self.cwd,thisBranch,self.hierStack[-1])
    return


  def scanDirectory(self,directory,branch,docID):
    """ recursively called function
    branch = string
    """
    logging.debug("scanDirectory docID: "+docID+"  end of path: "+directory[25:])
    contentDir = os.listdir(self.basePath+directory)
    # check all subbranches, projects, steps, tasks
    branch = branch.split("\n")
    numSpacesChilds = len(branch[1]) - len(branch[1].lstrip())
    for line in branch:
      if line.strip()=='': break
      if (len(line)-len(line.lstrip())) == numSpacesChilds:
        thatDocType, thatName, thatDocID, thatChildNum = line.split(": ")
        if thatDocID.startswith('t-'):
          dirName = self.createDirName(thatName,thatDocType.strip(),thatChildNum)
          if dirName in contentDir:
            #db-branch exists in folder
            contentDir.remove(dirName)
            subBranch = self.getSubBranch(branch, thatDocID)
            self.scanDirectory(directory+dirName+'/', subBranch, thatDocID)
          else:
            #db-branch does not exist in folder
            logging.error(" db-branch |"+thatName+"|"+dirName+"| does not exist in folder: "+directory)
        else:
          thatDocType = thatDocType.strip()
          if '//' in thatName:
            print("TODO how to compare if remote data")
          filePath = thatName.replace('.','_')+"_jams.json"
          print('\n\nHHH',thatName)
          self.compareDiskDB(thatDocID, directory+filePath)
          print("Debug",contentDir,filePath)
          contentDir.remove(os.path.basename(filePath))
    # handle known file in directory
    if 'id_jams.json' in contentDir:
      self.compareDiskDB(docID, directory+"id_jams.json")
      contentDir.remove('id_jams.json')
    # files in directory but not in DB
    for fName in contentDir:
      if fName.endswith("_jams.svg") or fName.endswith("_jams.png") or fName.endswith("_jams.jpg"):
        continue  #files that do not need to be accounted for
      if fName.endswith("_jams.json"):
        logging.warning("JAMS.json file dangling in folder: "+directory+"    fileName: "+fName)
        continue
      logging.warning("File in directory that are not in db: "+fName)
      # test if file already in database
      md5sum = hashlib.md5(open(self.basePath+directory+fName,'rb').read()).hexdigest()
      view = self.db.getView('viewMD5/viewMD5', key=md5sum)
      if len(view) > 0:
        logging.warning("File"+fName+" is already in db as id "+view[0]['id']+" with filename "+view[0]['value'])
      else:
        print("debug1",directory,fName)
        newDoc = self.getImage(directory+fName)
        parentDoc = self.db.getDoc(docID)
        hierStack = parentDoc['inheritance']+[docID]
        self.addData('measurement', newDoc, hierStack)
        logging.warning("added file "+fName+" is to database")
    return


  def getSubBranch(self, branch,docID):
    """
    branch = array
    """
    thisBranch  = ""
    numSpaces   = -1
    useLine     = False
    for line in branch:
      if line.strip()=='': break
      thatDocType, thatName, thatID, thatChildNum = line.split(": ")
      if thatID==docID:
        numSpaces = len(line)-len(line.lstrip())
        useLine     = True
      elif numSpaces==len(line)-len(line.lstrip()):
        useLine     = False
      if useLine:
        thisBranch += thatDocType+": "+thatName+": "+thatID+": "+thatChildNum+"\n"
    return thisBranch


  def compareDiskDB(self, docID, filePath):
    """
    filePath = not full path
    """
    docDisk = json.load(open(self.basePath+filePath, 'r'))
    docDB   = self.db.getDoc(docID)
    if docDisk == docDB:
      logging.info("Disk and database agree "+filePath+" id:"+docID)
    else:
      logging.error("Disk and database DO NOT agree "+filePath+" id:"+docID)
      logging.debug(json.dumps(docDB))
      logging.debug(json.dumps(docDisk))
    if 'md5sum' in docDB and docDB['md5sum']!='':
      md5sumDisk = hashlib.md5(open(self.basePath+docDB['name'],'rb').read()).hexdigest()
      if docDB['md5sum'] == md5sumDisk:
        logging.info("MD5sums agree")
      else:
        logging.error("MD5sums DO NOT agree")
        logging.debug(docDB)
    return

  def getImage(self, filePath):
    """
    get image from datafile: central distribution point
    - max image size defined here

    Args:
        filePath: path to file
    """
    maxSize = 600
    extension = os.path.splitext(filePath)[1][1:]
    pyFile = "image_"+extension+".py"
    pyPath = self.softwarePath+'/'+pyFile
    if '//' in filePath:
      outFile = self.basePath+self.cwd+os.path.basename(filePath).split('.')[0]+'_jams'
    else:
      outFile = self.basePath+filePath.replace('.','_')+'_jams'
    if os.path.exists(pyPath):
      # import module and use to get data
      module = importlib.import_module(pyFile[:-3])
      image, imgType, metaMeasurement = module.getImage(self.basePath+filePath)
      # depending on imgType: produce image
      if imgType == "line":  #no scaling
        figfile = StringIO()
        plt.savefig(figfile, format='svg')
        image = figfile.getvalue()
        # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
        if self.cwd is not None:
          with open(outFile+'.svg','w') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      elif imgType == "waves":
        ratio = maxSize / image.size[np.argmax(image.size)]
        image = image.resize((np.array(image.size)*ratio).astype(np.int)).convert('RGB')
        figfile = BytesIO()
        image.save(figfile, format='JPEG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        image = 'data:image/jpg;base64,' + imageData
        if self.cwd is not None:
          with open(outFile+'.jpg','wb') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      elif imgType == "contours":
        ratio = maxSize / image.size[np.argmax(image.size)]
        image = image.resize((np.array(image.size)*ratio).astype(np.int))
        figfile = BytesIO()
        image.save(figfile, format='PNG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        image = 'data:image/png;base64,' + imageData
        if self.cwd is not None:
          with open(outFile+'.png','wb') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      else:
        image, metaMeasurement = '', {'measurementType':''}
        logging.error('getImage Not implemented yet 1'+str(imgType))
    else:
      image, metaMeasurement = '', {'measurementType':''}
      logging.warning("getImage: could not find pyFile to convert"+pyFile)
    #produce meta information
    measurementType = metaMeasurement.pop('measurementType')
    meta = {'image': image, 'name': filePath, 'type': 'measurement', 'comment': '',
            'measurementType':measurementType, 'meta':metaMeasurement}
    meta['md5sum'] = hashlib.md5(open(self.basePath+filePath,'rb').read()).hexdigest()
    logging.info("Image successfully created")
    return meta


  def replicateDB(self, remoteDB=None, removeAtStart=False):
    """
    Replicate local database to remote database

    Args:
        remoteDB: if given, use this name for external db
        removeAtStart: remove remote DB before starting new
    """
    if remoteDB is not None:
      self.remoteDB['database'] = remoteDB
    self.db.replicateDB(self.remoteDB, removeAtStart)
    return


  ######################################################
  ### OUTPUT COMMANDS ###
  ######################################################
  def output(self, docLabel):
    """
    output view to screen
    - length of output 110 character

    Args:
        docLabel: document label to output
    """
    view = 'view'+docLabel
    outString = []
    docList = self.db.dataLabels+self.db.hierarchyLabels
    idx     = list(dict(docList).values()).index(docLabel)
    docType = list(dict(docList).keys())[idx]
    for item in self.db.dataDictionary[docType][0][docLabel]:
      key = list(item.keys())[0]
      if item['length']!=0:
        outputString = '{0: <'+str(abs(item['length']))+'}'
        outString.append(outputString.format(key) )
    outString = "|".join(outString)+'\n'
    outString += '-'*110+'\n'
    for lineItem in self.db.getView(view+'/'+view):
      rowString = []
      for idx, item in enumerate(self.db.dataDictionary[docType][0][docLabel]):
        key = list(item.keys())[0]
        if item['length']!=0:
          outputString = '{0: <'+str(abs(item['length']))+'}'
          if isinstance(lineItem['value'][idx], str ):
            formatString = lineItem['value'][idx]
          else:
            formatString = ' '.join(lineItem['value'][idx])
          if item['length']<0:  #test if value as non-trivial length
            if lineItem['value'][idx]=='true' or lineItem['value'][idx]=='false':
              formatString = lineItem['value'][idx]
            elif len(lineItem['value'][idx])>1 or len(lineItem['value'][idx][0])>3:
              formatString = 'true'
            else:
              formatString = 'false'
            # formatString = True if formatString=='true' else False
          rowString.append(outputString.format(formatString)[:abs(item['length'])] )
      outString += "|".join(rowString)+'\n'
    return outString


  def outputHierarchy(self, onlyHierarchy=True, addID=False):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same

    Args:
       onlyHierarchy: only print project,steps,tasks or print all (incl. measurements...)[default print all]
       addID: add docID to output
    """
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return
    projectID = self.hierStack[0]
    view = self.db.getView('viewHierarchy/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      if onlyHierarchy and not item['id'].startswith('t-'):
        continue
      nativeView[item['id']] = item['value']
    outString = cT.hierarchy2String(nativeView, addID)
    outString = outString.replace(': undefined\n',': -1\n')
    return outString


  def outputQR(self):
    """
    output list of sample qr-codes
    """
    outString = '{0: <36}|{1: <36}|{2: <36}'.format('QR', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewQR/viewQR'):
      outString += '{0: <36}|{1: <36}|{2: <36}'.format(item['key'][:36], item['value'][:36], item['id'][:36])+'\n'
    return outString


  def outputMD5(self):
    """
    output list of measurement md5-sums of files
    """
    outString = '{0: <32}|{1: <40}|{2: <25}'.format('MD5 sum', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewMD5/viewMD5'):
      outString += '{0: <32}|{1: <40}|{2: <25}'.format(item['key'], item['value'][-40:], item['id'])+'\n'
    return outString
