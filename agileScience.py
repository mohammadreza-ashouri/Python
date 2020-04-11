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
          data['path'] = self.cwd + self.createDirName(data['name'],data['type'],thisChildNumber)
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
            fileName = os.path.basename(data['name'])
            fileName, extension = os.path.splitext(fileName)
            data['path'] = self.cwd + cT.camelCase(fileName)+extension
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
        with open(self.basePath+data['path'].replace('.','_')+'_jams.json','w') as f:
          f.write(json.dumps(data))
    self.currentID = data['_id']
    logging.debug("Data saved "+data['_id']+' '+data['_rev']+' '+data['type'])
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
  ### Disk directory/folder methods
  ######################################################
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
        if self.cwd=='/': self.cwd=''
    else:  # existing project ID is given: open that
      self.hierStack.append(id)
      if self.cwd is not None:
        path = self.db.getDoc(id)['path']
        dirName = path.split('/')[-1]
        os.chdir(dirName)
        self.cwd += dirName+'/'
    return


  def scanTree(self, slow=True):
    """ Set up everything
    - branch refers to things in database
    - directories refers to things on harddisk
    """
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return
    # collect all information
    view = self.db.getView('viewHierarchy/viewPaths', key=self.hierStack[0])
    database = {}
    for item in view:
      thisPath = item['value'][0]
      if thisPath.startswith(self.cwd[:-1]):
        database[thisPath] = [item['id'], item['value'][1]]
    for path, _, files in os.walk('.'):
      path = os.path.normpath(self.cwd+path)
      if path in database:
        #database and directory agree regarding project/step/task
        docFile = json.load(open(self.basePath+path+'/id_jams.json'))
        if docFile['path']==path and docFile['_id']==database[path][0] and docFile['type']==database[path][1]:
          logging.debug(path+'fast test successful on project/step/task')
        else:
          logging.error(path+'fast test successful on project/step/task')
          logging.error(docFile['path'],docFile['_id'],docFile['type'])
          logging.error(path, database[path])
        if slow:
          docDB = self.db.getDoc(docFile['_id'])
          if docDB==docFile:
            logging.debug(path+'slow test successful on project/step/task')
          else:
            logging.error(path+'slow test UNsuccessful on project/step/task')
            logging.error(docDB)
            logging.error(docFile)
      else:
        print("ERROR** "+path+' directory (project/step/task) not in database')
      for file in files:
        if file == 'id_jams.json': continue
        if file.endswith('_jams.json'):
          jsonFileName = path+os.sep+file
          fileName = jsonFileName[:-10]
          if fileName[-4]=='_':
            fileName = fileName[:-4]+'.'+fileName[-3:]
        elif '_jams.' in file:
          continue
        else:
          fileName = path+os.sep+file
          jsonFileName = fileName.replace('.','_')+'_jams.json'
        if fileName in database:
          if database[fileName] is False:
            continue #do not verify data-file and its json file twice
          #database and directory agree regarding project/step/task
          docFile = json.load(open(self.basePath+jsonFileName))
          if docFile['path']==fileName and docFile['_id']==database[fileName][0] and docFile['type']==database[fileName][1]:
            logging.debug(fileName+' fast test successful on project/step/task')
          else:
            logging.error(fileName+' fast test successful on project/step/task')
            logging.error(docFile['path'],docFile['_id'],docFile['type'])
            #logging.error(fileName, database[fileName])
          if slow:
            docDB = self.db.getDoc(docFile['_id'])
            if docDB==docFile:
              logging.debug(fileName+' slow test successful on project/step/task')
            else:
              logging.error(fileName+' slow test UNsuccessful on project/step/task')
              logging.error(docDB)
              logging.error(docFile)
          database[fileName] = False #mark as already processed
        else:
          #not in database, create database entry
          logging.info(file+'| data not in database')
          filePath  = path+os.sep+file
          newDoc    = {'name':filePath}
          docID     = database[path][0]
          parentDoc = self.db.getDoc(docID)
          hierStack = parentDoc['inheritance']+[docID]
          self.addData('measurement', newDoc, hierStack)
      database[path] = False
    ## After all files are done
    if any(database.values()):
      logging.error("Database has documents that are not on disk")
      logging.error(database)
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
    absFilePath = self.basePath+filePath
    pyFile = "image_"+extension+".py"
    pyPath = self.softwarePath+'/'+pyFile
    if os.path.exists(pyPath):
      if '://' in absFilePath:
        outFile = self.basePath+self.cwd+os.path.basename(filePath).split('.')[0]+'_jams'
      else:
        outFile = absFilePath.replace('.','_')+'_jams'
      # import module and use to get data
      module = importlib.import_module(pyFile[:-3])
      image, imgType, metaMeasurement = module.getImage(absFilePath)
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
    meta['md5sum'] = hashlib.md5(open(absFilePath,'rb').read()).hexdigest()
    logging.info("Image successfully created")
    return meta


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
