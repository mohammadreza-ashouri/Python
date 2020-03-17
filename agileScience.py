import os, json, base64, hashlib
import importlib, traceback
import numpy as np
import matplotlib.pyplot as plt
import logging

# from asCouchDB import Database
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
    self.alive     = True
    return


  def exit(self):
    """
    Allows shutting down things
    """
    self.alive     = False
    logging.debug("\nEND JAMS")
    return

  ######################################################
  ### Change in database
  ######################################################
  def addData(self, docType, data, hierStack=[]):
    """
    Save data to data base, also after edit

    Logic is complicated: # TODO simplify logic with clear docTypes

    Args:
        docType: docType to be stored
        data: to be stored
        hierStack: hierStack from external functions
    """
    logging.info('jams.addData Got data: '+docType+' | '+str(hierStack))
    # logging.info(str(data))
    # collect data and prepare
    if docType == '-edit-':
      temp = self.db.getDoc(self.hierStack[-1])
      temp.update(data)
      data   = temp
      newDoc = False
    else:
      data['type'] = docType
      newDoc       = True
    if len(hierStack) == 0:
      hierStack = self.hierStack
    projectID = hierStack[0] if len(hierStack) > 0 else None
    if len(self.hierStack) > 0 and data['type'] != 'project':
      parent = self.db.getDoc(self.hierStack[-1])
    else:
      parent = None
    dirName = None
    if newDoc and self.cwd is not None:  #updated information keeps its dirName
      if data['type'] == 'project':
        dirName = cT.camelCase(data['name'])
      elif data['type'] in self.hierList:
        dirName = ("{:03d}".format(len(parent['childs'])))+'_'+cT.camelCase(data['name'])
      data['dirName'] = dirName
    # do default filling and save
    data = cT.fillDocBeforeCreate(data, docType, projectID).to_dict()
    _id, _rev = self.db.saveDoc(data)
    if 'image' in data:
      del data['image']
    logging.debug("Data saved "+str(data))
    if parent is not None:
      parent['childs'].append(_id)
      logging.debug("Parent updated "+str(parent))
      self.db.updateDoc(parent)
    if dirName is not None:  # create directory for projects,steps,tasks
      os.makedirs(dirName, exist_ok=True)
      with open(dirName+'/.id.txt','w') as f:
        f.write(_id)
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

    #TODO compare with database version and adopt database
          better inverse: search database and then get directory names and then use to 
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
        if project == cT.camelCase(item['key']):
          projectID = item['id']
      if projectID is None:
        logging.error("jams.scanDirectory No project found scanDirectory")
        return
      hierStack = [projectID]  # temporary version
      if step is not None:
        for itemID in self.db.getDoc(projectID)['childs']:
          if step == cT.camelCase(self.db.getDoc(itemID)['name']):
              stepID = itemID
        if stepID is None:
          logging.error("jams.scanDirectory No step found scanDirectory")
          return
        hierStack.append(stepID)
      if task is not None:
        for itemID in self.db.getDoc(stepID)['childs']:
          if task == cT.camelCase(self.db.getDoc(itemID)['name']):
            taskID = itemID
        if taskID is None:
          logging.error("jams.scanDirectory No task found scanDirectory")
          return
        hierStack.append(taskID)
      # loop through all files and process
      for fName in fNames:  # all files in this directory
        logging.info("Try to process for file:"+fName)
        if fName.endswith('_jams.svg') or fName.endswith('_jams.jpg') or fName == '.id.txt':
          continue
        # test if file already in database
        md5sum = hashlib.md5(open(fName,'rb').read()).hexdigest()
        view = self.db.getView('viewMeasurements/viewMD5', key=md5sum)
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
      image, imgType, meta = module.getImage(filePath)
      if 'measurementType' not in meta:
        logging.warning('getImage: measurementType should be set')
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
      meta['image']  = image
      meta['md5sum'] = hashlib.md5(open(filePath,'rb').read()).hexdigest()
      meta.update({'name': filePath, 'type': 'measurement', 'comment': '', 'alias': ''})
      logging.info("Image successfully created")
      return meta
    else:
      logging.warning("getImage: could not find pyFile to convert"+pFile)
      return None # default case if nothing is found

  def replicateDB(self, remoteDB=None):
    """
    Replicate local database to remote database

    Args:
        remoteDB: if given, use this name for external db
    """
    if remoteDB is not None:
      self.remoteDB['database'] = remoteDB
    self.db.replicateDB(self.remoteDB)
    return


  ######################################################
  ### OUTPUT COMMANDS ###
  ######################################################
  def output(self, docType):
    """
    output view to screen

    Args:
        docType: document type to output
    """
    view = 'view'+docType
    outString = ''
    if docType == 'Measurements':
      outString += '{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format('Name', 'Alias', 'Comment', 'Image', 'project-ID')+'\n'
    if docType == 'Projects':
      outString += '{0: <25}|{1: <6}|{2: >5}|{3: <38}|{4: <32}'.format('Name', 'Status', '#Tags', 'Objective', 'ID')+'\n'
    if docType == 'Procedures':
      outString += '{0: <25}|{1: <51}|{2: <32}'.format('Name', 'Content', 'project-ID')+'\n'
    if docType == 'Samples':
      outString += '{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format('Name', 'Chemistry', 'Comment', 'QR-code', 'project-ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView(view+'/'+view):
      if docType == 'Measurements':
        outString += '{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format(
          item['value'][0][:25], str(item['value'][1])[:21], item['value'][2][:21], str(item['value'][3]), item['key'])+'\n'
      if docType == 'Projects':
        outString += '{0: <25}|{1: <6}|{2: <5}|{3: <38}|{4: <32}'.format(
          item['key'][:25], item['value'][0][:6], item['value'][2], item['value'][1][:38], item['id'])+'\n'
      if docType == 'Procedures':
        outString += '{0: <25}|{1: <51}|{2: <32}'.format(
          item['value'][0][:25], item['value'][1][:51], item['key'])+'\n'
      if docType == 'Samples':
        outString += '{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format(
          item['value'][0][:25], item['value'][1][:15], item['value'][2][:27], str(item['value'][3]), item['key'])+'\n'
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
    view = self.db.getView('viewProjects/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      nativeView[item['id']] = item['value']
    outString = cT.projectDocsToString(nativeView, projectID, 0)
    return outString


  def outputQR(self):
    """
    output list of sample qr-codes
    """
    outString = '{0: <25}|{1: <40}|{2: <25}'.format('QR', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewSamples/viewQR'):
      outString += '{0: <25}|{1: <40}|{2: <25}'.format(item['key'], item['value'][:40], item['id'])+'\n'
    return outString


  def outputMD5(self):
    """
    output list of measurement md5-sums of files
    """
    outString = '{0: <32}|{1: <40}|{2: <25}'.format('MD5 sum', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewMeasurements/viewMD5'):
      outString += '{0: <32}|{1: <40}|{2: <25}'.format(item['key'], item['value'][-40:], item['id'])+'\n'
    return outString
