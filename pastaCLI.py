#!/usr/bin/python3
"""
COMMAND LINE INTERFACE
"""
import copy, json, os, sys, re, warnings
import subprocess, tempfile, base64, io, traceback
import asyncio
from pprint import pprint
import numpy as np
from PIL import Image
from questionary import prompt, Separator
#the package
from backend import Pasta
from miscTools import bcolors


###########################################################
### FUNCTIONS FOR USER INTERACTION
###########################################################
def confirm(doc=None, header=None):
  """
  Used as callback function: confirm that the given document should be written to database

  Args:
     doc (string): this is the content to be written
     header (string): some arbitrary information used as header

  Returns:
      bool: confirmation
  """
  print()
  if header is not None:
    print(f'{bcolors.BOLD}'+header+f'{bcolors.ENDC}')
  if isinstance(doc, dict):
    temp = doc.copy()
    if 'image'      in temp:                          temp['image'] = '[...]'
    if 'metaVendor' in temp:                          temp['metaVendor'] = '[...]'
    if 'new' in temp and 'image'      in temp['new']: temp['new']['image'] = '[...]'
    if 'new' in temp and 'metaVendor' in temp['new']: temp['new']['metaVendor'] = '[...]'
    if 'old' in temp and 'image'      in temp['old']: temp['old']['image'] = '[...]'
    if 'old' in temp and 'metaVendor' in temp['old']: temp['old']['metaVendor'] = '[...]'
    pprint(temp)
  elif isinstance(doc, str):
    print(doc)
  success = input("Is that ok? [Y/n] ")
  if success in ('n','N'):
    return False
  return True


def curate(doc):
  """
  Curate measurement by user: say measurement good/bad/ugly
  Used as callback function after information is automatically found
    requires global variable menuOutline

  Args:
     doc (dict): document found. Image attribute used for display

  Returns:
    bool: success of curation
  """
  questionsLocal = [  #T-O-D-O use global items
    {"type":"confirm", "name":"use_file",       "message":"Use this measurement?",       "default":True},
    {"type":"confirm", "name":"use_dir",        "message":"Use this directory?",         "default":True, "when": lambda x: not x["use_file"]},
    {"type":"input",   "name":"comment",        "message":"Comment, #tags, :field:1:?",  "default":"",   "when": lambda x:     x["use_file"]},
    {"type":"list",    "name":"sample",         "message":"Which sample was used?",                      "when": lambda x:     x["use_file"]},
    {"type":"list",    "name":"procedure",      "message":"Which procedure was used?",                   "when": lambda x:     x["use_file"]},
    {"type":"input",   "name":"measurementType","message":"Use other measurement type?",                 "when": lambda x:     x["use_file"]}
    ]
  print(f'\n{bcolors.BOLD}=> Curate measurement:'+doc['name']+f' <={bcolors.ENDC}')
  #show image
  if doc['image'].startswith('<?xml'):
    with open(tempfile.gettempdir()+os.sep+'tmpFilePASTA.svg','w') as outFile:
      outFile.write(doc['image'])
    # optional code if viewer (mac/windows) cannot display svg
    # cairosvg.svg2png(bytestring=doc['image'], write_to=tempfile.gettempdir()+os.sep+'tmpFilePASTA.png')
    viewer = subprocess.Popen(['display',tempfile.gettempdir()+os.sep+'tmpFilePASTA.svg' ])
  elif doc['image'].startswith('data:image'):  #for jpg and png
    imgdata = base64.b64decode(doc['image'][22:])
    image = Image.open(io.BytesIO(imgdata))
    print("Verify image mode in curate: ",image.mode)
    if image.mode=='P':
      warnings.simplefilter("ignore")  #some images might have transparency which is would trigger warning
      image = image.convert('RGB')
      warnings.simplefilter('default')
    image.save(tempfile.gettempdir()+os.sep+'tmpFilePASTA.jpg', format='JPEG')
    viewer = subprocess.Popen(['display',tempfile.gettempdir()+os.sep+'tmpFilePASTA.jpg' ])
  #prepare question and ask question and use answer
  for itemJ in questionsLocal:
    if itemJ['name']=='comment' and 'comment' in doc:
      itemJ['default'] = doc['comment']
    if itemJ['name']=='sample' or itemJ['name']=='procedure':
      docs = be.output(itemJ['name'], printID=True).split("\n")[2:-1]
      docs = [i.split('|')[0].strip()+' |'+i.split('|')[-1] for i in docs]
      itemJ['choices'] = ['--']+docs
  asyncio.set_event_loop(asyncio.new_event_loop())
  answerJ = prompt(questionsLocal)
  #clean open windows
  viewer.terminate()
  viewer.kill() #on windows could be skiped
  viewer.wait() #wait for process to close
  if os.path.exists(tempfile.gettempdir()+os.sep+'tmpFilePASTA.svg'):
    os.unlink(tempfile.gettempdir()+os.sep+'tmpFilePASTA.svg')
  if os.path.exists(tempfile.gettempdir()+os.sep+'tmpFilePASTA.jpg'):
    os.unlink(tempfile.gettempdir()+os.sep+'tmpFilePASTA.jpg')
  if len(answerJ)==0:  #ctrl-c hit
    return False
  if not answerJ['use_file']:
    doc['ignore'] = 'file'
    if not answerJ['use_dir']:
      doc['ignore'] = 'dir'
    return False
  #if measurement should be used
  doc['ignore'] = "none"
  if answerJ['measurementType']!='':
    doc['type']    = ['measurement', '', answerJ['measurementType']]
  if answerJ['comment']!='':
    doc['comment'] = answerJ['comment']
  if answerJ['sample']!='--':
    doc['sample'] = answerJ['sample'].split('|')[-1].strip()
  if answerJ['procedure']!='--':
    doc['procedure'] = answerJ['procedure'].split('|')[-1].strip()
  doc['curated'] = True
  return answerJ['measurementType']!=''  #True: rerun; False: no new scan is necessary


###########################################################
### MAIN FUNCTION
###########################################################
print("WARNING*** DISCONTINUED SOME TIME AGO. THIS IS AN OLD AND DEPRECATED VERSION")
pathSoftware = os.path.dirname(os.path.abspath(__file__))
menuOutline = json.load(open(pathSoftware+'/userInterfaceCLI.json', 'r')) # keep menus separate from dataDictionary since only CLI needs menu
if len(sys.argv)>1: configName=sys.argv[1]
else:               configName=None
be = Pasta(configName=configName, confirm=confirm)
print('Start in directory',os.path.abspath(os.path.curdir))
nextMenu = 'main'
while be.alive:
  #output the current hierarchical level
  if len(be.hierStack) == 0:
    try:
      print('\n==> You are at the root |'+be.cwd+'| <==')
    except:
      print('CWD not set:', be.cwd)
      sys.exit(1)
  else:
    levelName = be.hierList[len(be.hierStack)-1]
    objName   = be.getDoc(be.hierStack[-1])['name']
    print('\n==> You are in '+levelName+': '+objName+' |'+be.cwd+'| <==')
  #####################
  ### prepare menu  ###
  #####################
  if nextMenu in menuOutline and nextMenu != 'edit':
    #main and output menu are outlined in file, use those
    thisMenu = copy.deepcopy(menuOutline[nextMenu])
    questions = [{'type': 'list', 'name': 'choice', 'message': thisMenu[0], 'choices':[]}]
    for idx, item in enumerate(thisMenu):
      if idx == 0:
        continue
      if '---' in item:
        questions[0]['choices'].append(Separator())
        continue
      #extract properties of dictionary item
      append, expand = None, None
      if 'append' in item:
        append = item.pop('append')
      if 'expand' in item:
        expand = item.pop('expand')
      key, value = item.popitem()
      #use properties to augment questions
      if append is not None:
        if append == 'thisLevel':
          append = be.hierList[len(be.hierStack)-1] if len(be.hierStack) > 0 else None
        else:
          append = be.hierList[len(be.hierStack)] if len(be.hierStack) < len(be.hierList) else None
        if append is None:
          continue
        key   += ' '+append
        value += append
      if expand is None:
        expand = ['']
      else:
        if nextMenu == 'main':
          expand = [' '+i for i, j in be.dataLabels]
        else:  # output
          expand = [' '+i for i, j in be.dataLabels+be.hierarchyLabels]
      #create list of choices
      for itemI in expand:
        questions[0]['choices'].append({'name': key+itemI, 'value': value+itemI[1:]})
    if nextMenu != 'main':
      questions[0]['choices'].append({'name':'>Go back to main<', 'value':'menu_main'})
  elif nextMenu.startswith('change') or nextMenu in [i for i,j in be.dataLabels]:
    #change menu OR add/edit samples,procedures,measurements
    addEditDoc = nextMenu in [i for i,j in be.dataLabels]
    questions = [{'type': 'list', 'name': 'choice', 'message': nextMenu, 'choices':[]}]
    if len(be.hierStack) == 0 or addEditDoc: # no project in stack or sample/procedures/measurements: use VIEW
      if addEditDoc:
        view    = be.db.getView('viewDocType/'+nextMenu)
      else:
        view    = be.db.getView('viewDocType/project')
      values = [i['id'] for i in view]
      names  = [i['value'][0] for i in view]
    else:                      # step/task: get its children
      names, values = be.getChildren(be.hierStack[-1])
    if len(names)==0 and not addEditDoc:
      print('Nothing to choose from!')
      nextMenu = 'main'
      continue
    if addEditDoc:   prefix = 'direct_edit_'+nextMenu+'_'
    else:            prefix = 'function_changeHierarchy_'
    for name, value in zip(names, values):
      questions[0]['choices'].append({'name': name, 'value': prefix+value})
    if addEditDoc:
      questions[0]['choices'].append({'name': '>Add to '+nextMenu+'<', 'value': 'form_'+nextMenu})
    questions[0]['choices'].append({'name':'>Go back to main<', 'value':'menu_main'})
  else:  #form
    #ask for measurements, samples, procedures, projects, ...
    #create form (=sequence of questions for string input) is dynamically created from dataDictonary
    docType = nextMenu#.split('_')[1]
    if docType not in be.db.ontology:
      #got docLable not docType
      docType = [i[0] for i in be.dataLabels if i[1]==docType][0]
    heading = None
    questions = []
    for line in be.db.ontology[docType]:  # iterate over all data stored within this docType
      ### convert line into json-string that PyInquirer understands
      # decode incoming json
      if 'heading' in line:
        heading = line['heading']
      if 'query' not in line:               #skip if no query in item line
        continue
      itemList = line['list'] if 'list' in line else None
      name = line['name']
      questionString = line['query']
      if heading is not None:
        questionString = '--- '+heading +' ---\n'+questionString
        heading = None
      if 'unit' in line:
        questionString += ' ['+line['unit']+']'
      if 'required' in line and line['required']:
        questionString += ' *'
      # encode outgoing json
      question = {'type': 'input', 'name': name, 'message': questionString}
      if 'required' in line and line['required']:
        question['validate'] = lambda val: len(val.strip())>0
      if itemList is not None:
        question['type'] = 'list'
        if isinstance(itemList, list):
          question['choices'] = itemList
        else:
          try:
            itemList = be.output(itemList,printID=True).split("\n")[2:-1]
            itemList = [i.split('|')[0].strip()+' || '+i.split('|')[-1] for i in itemList]
          except:
            print('**ERROR** ontology for '+docType+' has faulty list')
            itemList = ['']
          question['choices'] = ['--']+itemList
      questions.append(question)
  #####################
  ### ask questions  ###
  #####################
  asyncio.set_event_loop(asyncio.new_event_loop())
  answer = prompt(questions)
  #####################
  ### handle answer ###
  #####################
  if 'choice' in answer:
    # forms that ask further questions
    answer = answer['choice'].split('_')
    if answer[0] == 'menu':
      nextMenu = answer[1]
    elif answer[0] == 'form':
      nextMenu = '_'.join(answer)
    else:   #function and direct
      res = None
      if answer[1] == 'edit': #direct
        if len(answer)==3: #edit project/step/task
          tmpFileName = tempfile.gettempdir()+os.sep+'tmpFilePASTA'+be.eargs['ext']
          inputString = be.getEditString()
        else:              #edit sample/procedure/measurements
          tmpFileName = tempfile.gettempdir()+os.sep+'tmpFilePASTA.json'
          inputString = json.dumps(be.getDoc(answer[-1]))
        with open(tmpFileName,'w') as fOut:
          fOut.write(inputString)
        os.system( be.eargs['editor']+' '+tmpFileName)
        with open(tmpFileName,'r') as fIn:
          if len(answer)==3:          #edit project/step/task
            be.setEditString(fIn.read(), callback=curate)
          else:                       #edit json for samples, procedures,...
            content = fIn.read()
            content = content.replace('\\\"',"'")  #get rid of all "
            matches = re.findall(r'(\"\"|\".[^\"]*\")',content)
            for oldString in matches:
              if "\n" in oldString:
                newString = oldString.replace("\n","\\n")
                content = content.replace(oldString,newString)
            try:
              be.addData('-edit-',json.loads(content))
            except:
              print('Error likely during json conversion\n'+traceback.format_exc())
        os.unlink(tmpFileName)
      elif len(answer) == 2: #function
        res = getattr(be, answer[1])(callback=curate)
      elif len(answer) > 2: #function
        res = getattr(be, answer[1])('_'.join(answer[2:]), callback=curate)
      if res is not None:
        if isinstance(res, bool):
          if res:     res='  Success'
          if not res: res='  Failure'
        print(res)  #output string returned from e.g. output-projects
      nextMenu = 'main'
  else:
    # all data collected, save it to database
    if nextMenu=='edit': #edit-> update data
      print("I SHOULD NOT BE HERE")
    elif len(answer)!=0 and np.sum([len(i) for i in list(answer.values())])>0:
      for key in answer:
        if ' || ' in answer[key]:
          answer[key] = answer[key].split('||')[-1].strip()  #get rid of prefix
      be.addData(docType, answer)
    else:
      print('Did not understand you.')
    nextMenu = 'main'
