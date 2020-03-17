import os, json, base64
import importlib, traceback
from io import StringIO, BytesIO
import numpy as np
import matplotlib.pyplot as plt
import logging

# from asCouchDB import Database
from asTools import imageToString, stringToImage
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

        Args:
           docType: docType to be stored
           data: to be stored
           hierStack: hierStack from external functions
        """
        logging.info('jams.addData Got data: '+docType+' | '+str(hierStack))
        logging.info(str(data))
        if docType == '-edit-':
            temp = self.db.getDoc(self.hierStack[-1])
            temp.update(data)
            data = temp
        else:
            data['type'] = docType
            if self.cwd is not None and data['type'] in self.hierList:  # create directory for projects,steps,tasks
                os.makedirs(cT.camelCase(data['name']), exist_ok=True)
        if len(hierStack) == 0:
            hierStack = self.hierStack
        projectID = hierStack[0] if len(hierStack) > 0 else None
        data = cT.fillDocBeforeCreate(data, docType, projectID).to_dict()
        _id, _rev = self.db.saveDoc(data)
        if 'image' in data:
            del data['image']
        logging.debug("Data saved "+str(data))
        if len(self.hierStack) > 0 and data['type'] != 'project':
            parent = self.db.getDoc(self.hierStack[-1])
            parent['childs'].append(_id)
            logging.debug("Parent updated "+str(parent))
            self.db.updateDoc(parent)
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
                name = self.db.getDoc(id)['name']
                os.chdir(cT.camelCase(name))
                self.cwd += cT.camelCase(name)+'/'
        return


    def scanDirectory(self):
        """ 
        Recursively scan directory tree for new files
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
                doc = self.getImage(os.path.join(root, fName))
                doc.update({'name': fName, 'type': 'measurement', 'comment': '', 'alias': ''})
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
                    image = image.resize((np.array(image.size)*ratio).astype(np.int)).convert('RGB')
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
                logging.info("Image successfully created")
                return meta
            except:
                logging.warning("Failure to produce image with "+pyFile+" with data file"+filePath+"\n"+traceback.format_exc())
        return None  # default case if nothing is found


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
