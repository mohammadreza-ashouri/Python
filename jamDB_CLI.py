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
from backend import JamDB
from miscTools import bcolors


### global parameters
pathSoftware = os.path.dirname(os.path.abspath(__file__))
menuOutline = json.load(open(pathSoftware+'/userInterfaceCLI.json', 'r')) # keep menus separate from dataDictionary since only CLI needs menu

### functions
def confirm(doc=None, header=None):
  """
  Used as callback function: confirm that the given document should be written to database
    required for initialization

  Args:
     doc: this is the content to be written
     header: some arbitrary information used as header
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
  Curate by user: say measurement good/bad/ugly
  Used as callback function after information is automatically found
    requires global variable menuOutline

  Args:
     doc: document found. Image attribute used for display
     menuOutline: outline of the menu of questions, userInterfaceCLI.json
  """
  print(f'\n{bcolors.BOLD}=> Curate measurement:'+doc['name']+f' <={bcolors.ENDC}')
  #show image
  if doc['image'].startswith('<?xml'):
    with open(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.svg','w') as outFile:
      outFile.write(doc['image'])
    # optional code if viewer (mac/windows) cannot display svg
    # cairosvg.svg2png(bytestring=doc['image'], write_to=tempfile.gettempdir()+os.sep+'tmpFilejamsDB.png')
    viewer = subprocess.Popen(['display',tempfile.gettempdir()+os.sep+'tmpFilejamsDB.svg' ])
  elif doc['image'].startswith('data:image'):  #for jpg and png
    imgdata = base64.b64decode(doc['image'][22:])
    image = Image.open(io.BytesIO(imgdata))
    print("Verify image mode in curate: ",image.mode)
    if image.mode=='P':
      warnings.simplefilter("ignore")  #some images might have transparency which is would trigger warning
      image = image.convert('RGB')
      warnings.simplefilter('default')
    image.save(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.jpg', format='JPEG')
    viewer = subprocess.Popen(['display',tempfile.gettempdir()+os.sep+'tmpFilejamsDB.jpg' ])
  #prepare question and ask question and use answer
  questions = menuOutline['curate']
  for itemJ in questions:
    if itemJ['name']=='comment' and 'comment' in doc:
      itemJ['default'] = doc['comment']
    if itemJ['name']=='sample':
      samples = be.output("Samples",printID=True).split("\n")[2:-1]
      samples = [i.split('|')[0].strip()+' |'+i.split('|')[-1] for i in samples]
      itemJ['choices'] = ['--']+samples
    if itemJ['name']=='procedure':
      procedures = be.output("Procedures",printID=True).split("\n")[2:-1]
      procedures = [i.split('|')[0].strip()+' |'+i.split('|')[-1] for i in procedures]
      itemJ['choices'] = ['--']+procedures
  asyncio.set_event_loop(asyncio.new_event_loop())
  answerJ = prompt(questions)
  #clean open windows
  viewer.terminate()
  viewer.kill() #on windows could be skiped
  viewer.wait() #wait for process to close
  if os.path.exists(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.svg'):
    os.unlink(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.svg')
  if os.path.exists(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.jpg'):
    os.unlink(tempfile.gettempdir()+os.sep+'tmpFilejamsDB.jpg')
  if len(answerJ)==0:  #ctrl-c hit
    return False
  if answerJ['measurementType']!='':
    doc['type']    = ['measurement', '', answerJ['measurementType']]
  if answerJ['comment']!='':
    doc['comment'] = answerJ['comment']
  if answerJ['sample']!='--':
    doc['sample'] = answerJ['sample'].split('|')[-1].strip()
  if answerJ['procedure']!='--':
    doc['procedure'] = answerJ['procedure'].split('|')[-1].strip()
  return answerJ['measurementType']!=''  #True: rerun; False: no new scan is necessary


###########################################################
### MAIN FUNCTION
###########################################################
if len(sys.argv)>1: configName=sys.argv[1]
else:               configName=None
be = JamDB(configName=configName, confirm=confirm)
print('Start in directory',os.path.abspath(os.path.curdir))
nextMenu = 'main'
while be.alive:
  #output the current hierarchical level
  if len(be.hierStack) == 0:
    print('\n==> You are at the root |'+be.cwd+'| <==')
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
    question = [{'type': 'list', 'name': 'choice', 'message': thisMenu[0], 'choices':[]}]
    for idx, item in enumerate(thisMenu):
      if idx == 0:
        continue
      if '---' in item:
        question[0]['choices'].append(Separator())
        continue
      #extract properties of dictionary item
      append, expand = None, None
      if 'append' in item:
        append = item.pop('append')
      if 'expand' in item:
        expand = item.pop('expand')
      key, value = item.popitem()
      #use properties to augment question
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
          expand = [' '+j for i, j in be.db.dataLabels]
        else:  # output
          expand = [' '+j for i, j in be.db.dataLabels+be.db.hierarchyLabels]
      #create list of choices
      for itemI in expand:
        question[0]['choices'].append({'name': key+itemI, 'value': value+itemI[1:]})
    if nextMenu != 'main':
      question[0]['choices'].append({'name':'>Go back to main<', 'value':'menu_main'})
  elif nextMenu.startswith('change') or nextMenu in [i for j,i in be.db.dataLabels]:
    #change menu OR add/edit samples,procedures,measurements
    addEditDoc = nextMenu in [i for j,i in be.db.dataLabels]
    question = [{'type': 'list', 'name': 'choice', 'message': nextMenu, 'choices':[]}]
    if len(be.hierStack) == 0 or addEditDoc: # no project in stack or sample/procedures/measurements: use VIEW
      if addEditDoc:
        view    = be.db.getView('view'+nextMenu+'/view'+nextMenu)
      else:
        view    = be.db.getView('viewProjects/viewProjects')
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
      question[0]['choices'].append({'name': name, 'value': prefix+value})
    if addEditDoc:
      question[0]['choices'].append({'name': '>Add to '+nextMenu+'<', 'value': 'form_'+nextMenu})
    question[0]['choices'].append({'name':'>Go back to main<', 'value':'menu_main'})
  else:  #form
    #ask for measurements, samples, procedures, projects, ...
    #create form (=sequence of questions for string input) is dynamically created from dataDictonary
    docType = nextMenu.split('_')[1]
    question = []
    if docType not in be.dataDictionary:  #only measurements, samples, procedures
      for type_, label_ in be.db.dataLabels:
        if label_ == docType:
          docType = type_
    for line in be.dataDictionary[docType]['default']:  # iterate over all data stored within this docType
      ### convert line into json-string that PyInquirer understands
      # decode incoming json
      itemList = line['list'] if 'list' in line else None
      name = line['name']
      questionString = line['long']
      generate = bool(len(questionString)==0)
      # encode outgoing json
      if generate:
        continue  # it is generated, no need to ask
      newQuestion = {'type': 'input', 'name': name, 'message': questionString}
      if itemList is not None:
        newQuestion['type'] = 'list'
      if isinstance(itemList, list):
        newQuestion['choices'] = itemList
      question.append(newQuestion)
  #####################
  ### ask question  ###
  #####################
  asyncio.set_event_loop(asyncio.new_event_loop())
  answer = prompt(question)
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
          tmpFileName = tempfile.gettempdir()+os.sep+'tmpFilejamsDB'+be.eargs['ext']
          inputString = be.getEditString()
        else:              #edit sample/procedure/measurements
          tmpFileName = tempfile.gettempdir()+os.sep+'tmpFilejamsDB.json'
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
        print(res)  #output string returned from e.g. output-projects
      nextMenu = 'main'
  else:
    # all data collected, save it
    if nextMenu=='edit': #edit-> update data
      print("I SHOULD NOT BE HERE")
    elif len(answer)!=0 and np.sum([len(i) for i in list(answer.values())])>0:
      be.addData(docType, answer)
    else:
      print('Did not understand you.')
    nextMenu = 'main'
