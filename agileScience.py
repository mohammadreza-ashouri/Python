#!/usr/bin/python3
import couchdb, json
import os, traceback
import copy
from PyInquirer import prompt
from pprint import pprint

# print all the documents
def printHierachy(id,level):
    """
    print hierachical structure in database, it is called recurselily
    """
    if id=="0":
        print("\n===== Hierachical content of database =====")
    doc = db.get(id)
    if doc is None:
        print("*** Found dead child",id)
        return
    if not 'name' in doc:
        print("*** No name in",id)
        return
    print("  "*level+doc['type']+": "+doc['name'],doc['_id'])
    for childID in doc['childs']:
        printHierachy(childID,level+1)
    return

def printData():
    """
    print all datat in list
    """
    for item in db.view('viewData/viewData'):
        print(item.key,'fileName',item.value)
    return

def printSamples():
    """
    print all samples in table form
    """
    print('key|name|chemistry|size')
    for item in db.view('viewData/viewSamples'):
        print(item.key,'|',item.value['name'],'|',item.value['chemistry'],'|',item.value['size'])
    return

############################
####  MAIN PROGRAM
############################
# open configuation file
user,password = None,None
with open(os.path.expanduser('~')+'/.agileScience.json') as jsonFile:
    data = json.load(jsonFile)
    user = data['user']
    password = data['password']
    databaseName = data['database']
    hierarchy    = data['hierarchy']
    allQuestions = data['questions']
    editorOptions= data['eargs']

# open server and get database
couch = couchdb.Server('http://'+user+':'+password+'@localhost:5984/')
try:
    db = couch[databaseName]
    print("Database exists")
except Exception:
    outString = traceback.format_exc().split('\n')
    if outString[-2]=="couchdb.http.ResourceNotFound":
        print("Database did not exist. Create it.")
        db = couch.create(databaseName)
    else:
        print("Something unexpected has happend")
        print('\n'.join(outString))
        db = None
if not "0" in db:  #create root
    db.save( {'type':'root', 'name':'root','_id':'0', 'childs':[]} ) 

# Questions for the CLI
level, idStack = -1, ['0']
questType = 'base'
while True:
    if level == -1:
        print("\n=====> You are at the root")
    else:
        print("\n=====> You are in "+hierarchy[level]+":",db.get(idStack[-1])['name'] )
    #prepare question
    questions = copy.deepcopy(allQuestions[questType])
    for key in questions[0].keys():
        value = questions[0][key]
        if '$next$' in value:
            value = value.replace('$next$',hierarchy[level+1])
        if key == 'choices':
            for choice in value[:]:
                if "$next$" in choice['name']:
                    if level<len(hierarchy):
                        choice['name'] = choice['name'].replace('$next$',hierarchy[level+1])
                    else:
                        value.remove(choice)
                if "$this$"  in choice['name'] and level==-1:
                    value.remove(choice)
                if "$this$" in choice['name']:
                    choice['name'] = choice['name'].replace('$this$',hierarchy[level])
                if "Open"   in choice['name'] and len(db.get(idStack[0])['childs'])==0:
                    value.remove(choice)
            if len(value)==0:
                listItems = {}
                for id in db.get(idStack[-1])['childs']:
                    if db.get(id)['type']==hierarchy[level+1]:
                        listItems[db.get(id)['name']] = id 
                value = listItems.keys()
        questions[0][key] = value
    if questType == 'edit':
      questions[0]["eargs"]=editorOptions
      questions[0]['default']=db.get(idStack[-1])['comment']
    #ask question
    doc = prompt(questions)
    #handle answers
    if 'choice' in doc:     #handle base questions
        if doc['choice'] == 'exit': break
        if doc['choice'] == 'close':
            level -= 1
            idStack.pop()
        if doc['choice'] in allQuestions.keys():
            questType = doc['choice']
            continue
    if questType=='open':  #handle second hierachy questions
        level += 1
        idStack.append( listItems[doc['target']] )
    elif questType=='edit':
        tempDoc = db.get(idStack[-1])
        tempDoc['comment'] = doc['text']
        db.save(tempDoc)
    elif questType=="close":
        print("Just close does nothing")
    elif questType=='print' and doc['choice'] == 'printHier':   
        printHierachy("0",0)
    elif questType=='print' and doc['choice'] == 'printSamp':   
        printSamples()
    elif questType=='print' and doc['choice'] == 'printData':   
        printData()
    else:
        if questType == "new":
            doc['type']   = hierarchy[level+1]
        else:
            doc['type']   = questType
        doc['childs'] = []
        reply = db.save(doc)
        if level>-1 and 'link' in doc and doc['link'] == True:
            parent = db.get(idStack[-1])
            parent['childs'].append(reply[0])
            db[parent.id] = parent
        if 'link' in doc:  del doc['link']
    questType = 'base'


"""
Things that Niels does not like at CouchDB
- mongoDB: collections; couchDB: type
- view Documents start with _design
- tag/keyword
- field: key:value; is everybody allowed to do add that; required fields are required
- alias file names, defaults to real
- logging (there is a revision history: no need to add logging)
- mongoDB/couchDB: comments are embedded json document
- mongoDB: identified, verified values; couchDB, use verificator, id as separate

- classes, inherited
- access: in couchdb is database based: too complicated

"""