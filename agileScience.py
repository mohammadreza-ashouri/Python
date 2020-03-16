import os, json, base64
import importlib, traceback
from io import StringIO, BytesIO
import numpy as np
import matplotlib.pyplot as plt
from asTools import imageToString, stringToImage
# from asCouchDB import Database
from asCloudant import Database
from commonTools import commonTools as cT

class AgileScience:
  """ PYTHON BACKEND 
  """
  def __init__(self, databaseName=None):
    """
    open server and define database

    Args:
        databaseName: name of database, otherwise taken from config file
    """
    # open configuration file and define database
    jsonFile = open(os.path.expanduser('~')+'/.agileScience.json')
    configuration = json.load(jsonFile)
    user         = configuration["user"]
    password     = configuration["password"]
    databaseName = configuration["database"] if databaseName is None
    self.db = Database(user,password,databaseName)
    self.remoteDB= configuration["remote"]
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
      print("Base folder did not exist. No directory saving\n",self.cwd)
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
    return
  
  ######################################################
  ### Change in database
  ######################################################
  def addData(self,docType,data, hierStack=None):
    """
    Save data to data base, also after edit

    Args:
       docType: docType to be stored
       data: to be stored
       hierStack: hierStack from external functions
    """
    if docType == '-edit-':
      temp = self.db.getDoc(self.hierStack[-1])      
      temp.update(data)
      data = temp
    else:
      data['type'] = docType
      if self.cwd is not None and data['type'] in self.hierList:  #create directory for projects,steps,tasks
        os.makedirs( cT.camelCase(data['name']), exist_ok=True )
    if hierStack is None:
      hierStack = self.hierStack
    projectID = hierStack[0] if len(hierStack)>1 else None
    data = cT.fillDocBeforeCreate(data, docType, projectID).to_dict()
    _id, _rev = self.db.saveDoc(data)
    if 'image' in data:
      del data['image']
    print("Data saved",data)
    if len(self.hierStack)>0 and data['type']!='project':
      parent = self.db.getDoc(self.hierStack[-1])
      parent['childs'].append(_id)
      print("Parent updated",parent)
      self.db.updateDoc(parent)
    return
  

  ######################################################
  ### Get data from database
  ######################################################
  def getDoc(self,id):
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
    if id in self.hierList:  #"project", "step", "task" are given: close
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-2])+'/'
    else:                    #existing project ID is given: open that
      self.hierStack.append(id)
      if self.cwd is not None:
        name = self.db.getDoc(id)['name']
        os.chdir( cT.camelCase(name) )
        self.cwd += cT.camelCase(name)+'/'
    return


  def scanDirectory(self):
    """ 
    Recursively scan directory tree for new files and print
    """
    for root,_,fNames in os.walk(self.cwd):
      # find directory names
      if len(fNames)==0:
        continue
      relpath = os.path.relpath(root,start=self.baseDirectory)
      if len(relpath.split('/'))==3:
        project,step,task = relpath.split('/')
      elif len(relpath.split('/'))==2:
        project,step = relpath.split('/')
        task = None
      elif len(relpath.split('/'))==1:
        project,step,task = relpath.split('/')[0], None, None
      else:
        project,step,task = None, None, None
        print("Error")
      # find IDs to names
      projectID, stepID, taskID = None, None, None
      for item in self.db.getView('viewProjects/viewProjects'):
        if project == cT.camelCase(item['key']):
          projectID = item['id']
      if projectID is None:
        print("**ERROR** No project found scanDirectory")
        return
      hierStack = [projectID]  #temporary version
      if step is not None:
        for itemID in self.db.getDoc(projectID)['childs']:
          if step == cT.camelCase(self.db.getDoc(itemID)['name']):
            stepID = itemID
        if stepID is None:
          print("**ERROR** No step found scanDirectory")
          return
        hierStack.append(stepID)
      if task is not None:
        for itemID in self.db.getDoc(stepID)['childs']:
          if task == cT.camelCase(self.db.getDoc(itemID)['name']):
            taskID = itemID
        if taskID is None:
          print("**ERROR** No task found scanDirectory")
          return
        hierStack.append(taskID)
      # loop through all files and process
      for fName in fNames:  #all files in this directory
        print("\n\nTry to process for file:",fName)
        doc = self.getImage(os.path.join(root,fName))
        doc.update({'name':fName, 'type':'measurement', 'comment':'','alias':''})
        self.addData('measurement',doc,hierStack)
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
    for pyFile in os.listdir(self.softwareDirectory):
      if not pyFile.startswith("image_"+extension):
        continue
      try:
        module = importlib.import_module(pyFile[:-3])
        image, imgType, meta = module.getImage(filePath)
        if imgType == "line":
          figfile = StringIO()
          plt.savefig(figfile, format='svg')
          image = figfile.getvalue()
          # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
        elif imgType == "waves":
          ratio = maxSize / image.size[np.argmax(image.size)]
          image = image.resize( (np.array(image.size)*ratio).astype(np.int) ).convert('RGB')
          figfile = BytesIO()
          image.save(figfile, format='JPEG')
          imageData = base64.b64encode(figfile.getvalue())
          if not isinstance(imageData, str):   # Python 3, decode from bytes to string
              imageData = imageData.decode()
          image = 'data:image/jpg;base64,' + imageData
        elif imgType == "contours":
          image = image
        else:
          raise NameError('**ERROR** Implementation failed')
        meta['image'] = image
        print("Image successfully created")
        return meta
      except:
        print(traceback.format_exc())
        print("Failure to produce image with",pyFile," with data file", filePath)
        print("Try next file")
    return None         #default case if nothing is found


  def replicateDB(self):
    """
    Replicate local database to remote database
    """
    self.db.replicateDB(self.remoteDB)
    return


  ######################################################
  ### OUTPUT COMMANDS ###
  ######################################################
  def output(self,docType):
    """
    output view to screen

    Args:
        docType: document type to print
    """
    view = 'view'+docType
    if docType=='Measurements':
      print('{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format('Name','Alias','Comment','Image','project-ID'))
    if docType=='Projects':
      print('{0: <25}|{1: <6}|{2: >5}|{3: <38}|{4: <32}'.format('Name','Status','#Tags','Objective','ID'))
    if docType=='Procedures':
      print('{0: <25}|{1: <51}|{2: <32}'.format('Name','Content','project-ID'))
    if docType=='Samples':
      print('{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format('Name','Chemistry','Comment','QR-code','project-ID'))
    print('-'*110)
    for item in self.db.getView(view+'/'+view):
      if docType=='Measurements':
        print('{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format(
          item['value'][0][:25],str(item['value'][1])[:21],item['value'][2][:21],str(item['value'][3]),item['key']))
      if docType=='Projects':
        print('{0: <25}|{1: <6}|{2: <5}|{3: <38}|{4: <32}'.format(
          item['key'][:25],item['value'][0][:6],item['value'][2],item['value'][1][:38],item['id']))
      if docType=='Procedures':
        print('{0: <25}|{1: <51}|{2: <32}'.format(
          item['value'][0][:25],item['value'][1][:51],item['key']))
      if docType=='Samples':
        print('{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format(
          item['value'][0][:25],item['value'][1][:15],item['value'][2][:27],str(item['value'][3]),item['key']))
    print("\n\n")
    return


  def outputHierarchy(self):
    """
    print hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same
    """
    if len(self.hierStack)==0:
      print('**WARNING** No project selected')
      return
    projectID = self.hierStack[0]
    view = self.db.getView('viewProjects/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      nativeView[item['id']] = item['value']
    outString = cT.projectDocsToString(nativeView, projectID,0)
    print(outString)
    return
