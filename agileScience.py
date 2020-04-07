""" Python Backend
"""
import os, json, base64, hashlib
import importlib, traceback
import numpy as np
import matplotlib.pyplot as plt
import logging
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
    logging.basicConfig(filename='jams.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
    logging.debug("\nSTART JAMS")
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
    # open basePath as current working directory
    self.softwareDirectory = os.path.abspath(os.getcwd())
    self.cwd     = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    self.baseDirectory = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    if not self.cwd.endswith("/"):
        self.cwd += "/"
    if os.path.exists(self.cwd):
        os.chdir(self.cwd)
    else:
        logging.warning("Base folder did not exist. No directory saving\n"+self.cwd)
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
    os.chdir(self.softwareDirectory)
    self.db.exit(deleteDB)
    self.alive     = False
    logging.debug("\nEND JAMS")
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
      if docType in self.hierList:  #should not have childnumber in other cases for debugging
        if docType=='project':
          data['childNum'] = 0
        else:
          thisStack = ' '.join(self.hierStack)
          view = self.db.getView('viewHierarchy/viewHierarchy', key=self.hierStack[0]) #not faster with cT.getChildren
          thisChildNumber = 0
          for item in view:
            if item['value'][2]=='project': continue
            if item['value'][0] == thisStack:
              thisChildNumber += 1
          data['childNum'] = thisChildNumber
      # find directory name
      dirName = None
      if newDoc and self.cwd is not None:  #updated information keeps its dirName
        if data['type'] == 'project':
          dirName = cT.camelCase(data['name'])
        elif data['type'] in self.hierList:  #steps, tasks
          dirName = ("{:03d}".format(thisChildNumber))+'_'+cT.camelCase(data['name'])
        data['dirName'] = dirName
      # do default filling and save
      if docType in self.hierList:
        prefix = 't'
      else:
        prefix = docType[0]
      data = cT.fillDocBeforeCreate(data, docType, hierStack, prefix).to_dict()
      _id, _rev = self.db.saveDoc(data)
      # create directory for projects,steps,tasks
      if dirName is not None:
        os.makedirs(dirName, exist_ok=True)
        with open(dirName+'/.idJAMS.txt','w') as f:
          f.write(_id)
    else:
      #update document
      data = cT.fillDocBeforeCreate(data, '--', hierStack[:-1], '--').to_dict()
      _id, _rev = self.db.updateDoc(data,self.hierStack[-1])
    self.currentID = _id
    # reduce information before logging
    if 'image' in data: del data['image']
    if 'meta'  in data: data['meta']='length='+str(len(data['meta']))
    logging.debug("Data saved "+str(data))
    return


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
        dirName = self.db.getDoc(id)['dirName']
        os.chdir(dirName)
        self.cwd += cT.camelCase(dirName)+'/'
    return


  def scanDirectory(self):
    """
    Recursively scan directory tree for new files

    #TODO compare directory tree with database version and adopt database
          better inverse:
          - search database and then get directory names from it
          - and use stored .id.txt file
    """
    for root, _, fNames in os.walk(self.cwd):
      # find directory names
      if len(fNames) == 0:
        continue
      relpath = os.path.relpath(root, start=self.baseDirectory)
      if len(relpath.split('/')) == 3:
        project, step, task = relpath.split('/')
      elif len(relpath.split('/')) == 2:
        project, step = relpath.split('/')
        task = None
      elif len(relpath.split('/')) == 1:
        project, step, task = relpath.split('/')[0], None, None
      else:
        project, step, task = None, None, None
        logging.error("jams.scanDirectory Error 1")
      # find IDs to names
      projectID, stepID, taskID = None, None, None
      for item in self.db.getView('viewProjects/viewProjects'):
        if project == cT.camelCase(item['value'][0]):
          projectID = item['id']
      if projectID is None:
        logging.error("jams.scanDirectory No project found scanDirectory")
        return
      view = self.db.getView('viewHierarchy/viewHierarchy', key=projectID)
      nativeView = {}
      for item in view:
        nativeView[item['id']] = item['value']
      hierStack = [projectID]  # temporary version
      if step is not None:
        for itemID in cT.getChildren(nativeView,projectID):
          if step == cT.camelCase(self.db.getDoc(itemID)['name']):
              stepID = itemID
        if stepID is None:
          logging.warning("jams.scanDirectory No step found scanDirectory")
        else:
          hierStack.append(stepID)
      if task is not None and stepID is not None:
        for itemID in cT.getChildren(nativeView,stepID):
          if task == cT.camelCase(self.db.getDoc(itemID)['name']):
            taskID = itemID
        if taskID is None:
          logging.warning("jams.scanDirectory No task found scanDirectory")
        else:
          hierStack.append(taskID)
      # loop through all files and process
      for fName in fNames:  # all files in this directory
        logging.info("Try to process for file:"+fName)
        if fName.endswith('_jams.svg') or fName.endswith('_jams.jpg') or fName == '.idJAMS.txt':
          continue
        # test if file already in database
        md5sum = hashlib.md5(open(fName,'rb').read()).hexdigest()
        view = self.db.getView('viewMD5/viewMD5', key=md5sum)
        if len(view) > 0:
          logging.warning("File"+fName+" is already in db as id "+view[0]['id']+" with filename "+view[0]['value'])
        else:
          doc = self.getImage(os.path.join(root, fName))
          self.addData('measurement', doc, hierStack)
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
    pyPath = self.softwareDirectory+'/'+pyFile
    if os.path.exists(pyPath):
      module = importlib.import_module(pyFile[:-3])
      image, imgType, metaMeasurement = module.getImage(filePath)
      if 'measurementType' in metaMeasurement:
        measurementType = metaMeasurement.pop('measurementType')
      else:
        logging.error('getImage: measurementType should be set')
        measurementType = ''
      if imgType == "line":  #no scaling
        outFile = os.path.splitext(filePath)[0]+"_jams.svg"
        plt.savefig(outFile)
        image = open(outFile,'r').read()
        # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
      elif imgType == "waves":
        ratio = maxSize / image.size[np.argmax(image.size)]
        image = image.resize((np.array(image.size)*ratio).astype(np.int)).convert('RGB')
        outFile = os.path.splitext(filePath)[0]+"_jams.jpg"
        image.save(outFile)
        imageData = base64.b64encode(open(outFile,'rb').read())
        image = 'data:image/jpg;base64,' + imageData.decode()
      elif imgType == "contours":
        image = image
        logging.error("getImage Not implemented yet 1")
        return None
      else:
        raise NameError('**ERROR** Implementation failed')
      meta = {'image': image, 'name': filePath, 'type': 'measurement', 'comment': '',
              'measurementType':measurementType, 'meta':metaMeasurement}
      meta['md5sum'] = hashlib.md5(open(filePath,'rb').read()).hexdigest()
      logging.info("Image successfully created")
      return meta
    else:
      logging.warning("getImage: could not find pyFile to convert"+pFile)
      return None # default case if nothing is found


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


  def outputHierarchy(self):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same
    """
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return
    projectID = self.hierStack[0]
    view = self.db.getView('viewHierarchy/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      nativeView[item['id']] = item['value']
    outString = cT.hierarchy2String(nativeView)
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
