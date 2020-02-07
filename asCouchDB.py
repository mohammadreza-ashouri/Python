import os, traceback
import couchdb, json
from asTools import string2TagFieldComment, camelCase, imageToString


class Database:
  def __init__(self):
    """
    open server and define database
    - verify hierarchyRoot is in database
    - verify dataDictionary is in database
    - verify userInterface is in database
    """
    # open configuration file and define database
    jsonFile = open(os.path.expanduser('~')+'/.agileScience.json')
    configuration = json.load(jsonFile)
    user         = configuration["user"]
    password     = configuration["password"]
    databaseName = configuration["database"]
    self.basePath     = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    if not self.basePath.endswith("/"):
      self.basePath += "/"
    if os.path.exists(self.basePath):
      os.chdir(self.basePath)
    else:
      print("Base folder did not exist. No directory saving\n",self.basePath)
      self.basePath   = None
    couch        = couchdb.Server("http://"+user+":"+password+"@localhost:5984/")
    self.eargs   = configuration["eargs"]
    try:
      self.db = couch[databaseName]
    except Exception:
      outString = traceback.format_exc().split("\n")
      if outString[-2]=="couchdb.http.ResourceNotFound":
          print("Database did not exist. Create it.")
          self.db = couch.create(databaseName)
      else:
          print("Something unexpected has happend")
          print("\n".join(outString))
          self.db = None
    if not "-hierarchyRoot-" in self.db:  #create root
        self.db.save( {"_id":"-hierarchyRoot-", "childs":[],"name":"root","type":""} )
    if not "-dataDictionary-" in self.db:
      print("**ERROR** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json",'r'))
      reply = self.db.save(dataDictionary)
    if not "-userInterface-" in self.db:
      print("**ERROR** User interaction not defined. Use default one")
      dataDictionary = json.load(open("userInterface.json",'r'))
      reply = self.db.save(dataDictionary)
    self.hierarchyList = self.db.get("-dataDictionary-")["-hierarchy-"]
    self.hierarchyStack = ['-hierarchyRoot-']
    self.hierarchyLevel = 0
  

  def getQuestions(self):
    """
    executed after database is intialized: create all questions
    - based on data dictionary stored in DB
    - add output, default questions
    """
    doc = self.db.get("-dataDictionary-")
    allNewQuestions = self.db.get("-userInterface-")
    for data in doc:            #iterate through each data-set entry: e.g. measurement
      if data.startswith("_") or data.startswith("-"):
        continue
      newQuestions = []
      for question in doc[data]: #iterate over all data stored within this data-set
        ### convert question into json-string that PyInquirer understands
        # decode incoming json
        keywords = {"list":None,"required":True,"generate":False,"default":None}
        for item in keywords:
          if item in question:
            keywords[item] = question[item]
            del question[item]
        if len(question)>1: print("**ERROR** QUESTION ILLDEFINED",question)
        name, questionString = question.popitem()
        # encode outgoing json
        newQuestion = {"type":"input","name": name,"message": questionString}
        newQuestions.append(newQuestion)
      newQuestions.append({"type":"input","name":"comment","message":"#tags, :field:value: comments"})
      if data not in self.hierarchyList:
        newQuestions.append({"type":"confirm","name": "linked","message": "Linked to hierarchy?","default": True})
      allNewQuestions[data] = newQuestions
    return allNewQuestions


  def questionCleaner(self,questions):
    """
    Clean questions to go into interface
    - fill the required lists
    - remove choices that are insensible
    - add default content

    Args:
       questions: to be cleaned
    """
    if self.hierarchyList[-1] != "--marker--":
      self.hierarchyList.append("--marker--")
    jsonString = json.dumps(questions)
    jsonString = jsonString.replace("$thisLevel$",self.hierarchyList[self.hierarchyLevel-1])
    jsonString = jsonString.replace("$nextLevel$",self.hierarchyList[self.hierarchyLevel])
    jsonObj    = json.loads(jsonString)
    ## changes based on next question
    if "type" not in jsonObj:   #if not an expand or list type
      return jsonObj
    if jsonObj['type'] == 'expand':
      for item in jsonObj:
        if item != "choices": continue
        jsonObj[item] = [i for i in jsonObj[item] if "--marker--" not in i["name"]]
    ## create list of sub-hierarchy
    if jsonObj['type'] == 'list' and len(jsonObj['choices'])==0:
      listItems = []
      for id in self.db.get(self.hierarchyStack[-1])['childs']:
        if self.db.get(id)['type']==self.hierarchyList[self.hierarchyLevel]:
          listItems.append(self.db.get(id)['type']+"_"+self.db.get(id)['name']+"_"+id) 
      jsonObj['choices'] = listItems
    if jsonObj['type']  == 'editor':
      jsonObj['eargs']   = self.eargs
      doc = self.db.get(self.hierarchyStack[-1])
      jsonObj['default'] = ", ".join(['#'+tag for tag in doc['tags']])+' '+doc['comment']
    return jsonObj


  def addData(self,question,data):
    """
    Save data to data base, also after edit

    Args:
       question: what question triggered the answer
       data: answer of question
    """
    if len(data)<1:   #no data returned from user
      return
    inputString = data['comment']
    if question == '-edit-':
      data = self.db.get(self.hierarchyStack[-1])
      flagLinked = False    #should not change
    else:
      data['type'] = question
      data['childs'] = []
      flagLinked = False
      if "linked" in data and data['linked'] and self.hierarchyLevel>0:
        flagLinked = True
      #images
      if data['type'] == 'measurement':
        print(data)
        if data['alias'] =='':  data['alias']=data['name']
        data['image'] = imageToString(data['name'])
    data.update(  string2TagFieldComment(inputString) )
    print("Data saved",data)
    _id, _rev = self.db.save(data)
    if question in self.hierarchyList or flagLinked:
      parent = self.db.get(self.hierarchyStack[-1])
      parent['childs'].append(_id)
      self.db[parent.id] = parent
    if self.basePath is not None:
      os.makedirs( camelCase(data['name']) )
    return


  def changeHierarchy(self, document):
    """
    Change through text hierarchy structure

    Args:
       document: information on how to change
    """
    if document == "-close-":
      self.hierarchyLevel -= 1
      self.hierarchyStack.pop()
      if self.basePath is not None:
        os.chdir('..')
      return
    listItems = document['choice'].split("_")
    if len(listItems)==3:
      levelName, name, id  = listItems
      levelIdx = self.hierarchyList.index(levelName)
      self.hierarchyLevel = levelIdx+1
      self.hierarchyStack.append(id)
      if self.basePath is not None:
        print(camelCase(name))
        os.chdir( camelCase(name) )
    else:
      print("** ERROR ** change Hierarchy")
    return


  ### OUTPUT COMMANDS ###
  def outputHierarchy(self,id,level=0):
    """
    print hierarchical structure in database, it is called recursively

    Args:
       id: database id
       level: hierarchical level (should not be used by user)
    """
    if id=="-hierarchyRoot-":
        print("\n===== Hierarchical content of database =====")
    doc = self.db.get(id)
    if doc is None or "name" not in doc or "type" not in doc: 
        print("*** Found incomplete child",id,"in parent")
        return
    print("  "*level+doc["type"]+": "+doc["name"],doc["_id"])
    for childID in doc["childs"]:
        self.outputHierarchy(childID,level+1)
    return


  def outputMeasurements(self):
    """
    print all measurements in list
    """
    for item in self.db.view("viewData/viewMeasurements"):
        print(item.key,"fileName",item.value)
    return


  def outputSamples(self):
    """
    print all samples in table form
    """
    print("key|name|chemistry|size")
    for item in self.db.view("viewData/viewSamples"):
        print(item.key,"|",item.value["name"],"|",item.value["chemistry"],"|",item.value["size"])
    return


  def outputProcedures(self):
    """
    print all procedures in table form
    """
    for item in self.db.view("viewData/viewProcedures"):
        print(item.key,"|",item.value["name"],"|",item.value["content"],"|")
    return
