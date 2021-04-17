#!/usr/bin/python3
""" Main function when command-line commands used

Problem:
pastaDB.py saveHierarchy --docID t-d4e64235040d232e1f7a71ca0564a9a1 --content "TestingNow||t-d4e64235040d232e1f7a71ca0564a9a1\n* Test\n* Hans\n** Wurst"

Called by user or reactElectron frontend. Keep it simple: only functions that
are required by frontend. Otherwise, make only temporary changes
"""
import os, json, sys, subprocess
import argparse, traceback
from backend import Pasta
from miscTools import upOut, getExtractorConfig

argparser = argparse.ArgumentParser(usage='''
pastaDB.py <command> [-i docID] [-c content] [-l labels] [-d database] [-p path]

Possible commands are:
    help: help information
    test: test PASTA setup
    updatePASTA: git pull in source
    verifyDB: test PASTA database
    saveBackup,loadBackup: save to file.zip / load from file.zip
    sync: synchronize / replicate with remote server
    print: print overview
        label: possible docLabels 'Projects', 'Samples', 'Measurements', 'Procedures'
    scanHierarchy, hierarchy: scan / print project
        item: documentID for. To be identified by printing Project
    saveHierarchy: save hierarchy to database
    addDoc:
      content is required as json-string
    newDB: add/update database configuration. item is e.g.
        '{"test":{"user":"Peter","password":"Parker",...}}'
    extractorTest: test the extractor of this file
        -p should be specified is the path to file from base folder
    extractorScan: get list of all extractors
''')
argparser.add_argument('command', help='help, test, updatePASTA, verifyDB, saveBackup, loadBackup, print, scanHierarchy, saveHierarchy, addDoc, hierarchy, newDB, extractorTest, extractorScan')
argparser.add_argument('-i','--docID',   help='docID of project', default='')
argparser.add_argument('-c','--content', help='content to save/store/extractorTest', default=None)
argparser.add_argument('-l','--label',   help='label used for printing', default='project')
argparser.add_argument('-p','--path',    help='path for extractor test', default='')
argparser.add_argument('-d','--database',help='name of database configuration', default='') #required for be = Pasta(args.database)
args = argparser.parse_args()

## general things that do not require open database
if args.command=='newDB':
  #use new database configuration and store in local-config file
  newDB = json.loads(args.item)
  label = list(newDB.keys()).pop()
  with open(os.path.expanduser('~')+'/.pasta.json','r') as f:
    configuration = json.load(f)
  configuration[label] = newDB[label]
  with open(os.path.expanduser('~')+'/.pasta.json','w') as f:
    f.write(json.dumps(configuration, indent=2))
elif args.command=='help':
  print("HELP:")
  argparser.print_help()
elif args.command=='up':
  print('up:',upOut(args.docID))
elif args.command=='extractorScan':
  pathToExtractors = os.path.dirname(os.path.abspath(__file__))+os.sep+'extractors'
  extractors = getExtractorConfig(pathToExtractors)
  extractors = [extractors[i]['plots'] for i in extractors if len(extractors[i]['plots'])>0 ] #remove empty entries
  extractors = [i for sublist in extractors for i in sublist]   #flatten list
  extractors = {'/'.join(i):j for (i,j) in extractors}
  with open(os.path.expanduser('~')+'/.pasta.json','r') as f:
    configuration = json.load(f)
  configuration['-extractors-'] = extractors
  with open(os.path.expanduser('~')+'/.pasta.json','w') as f:
    f.write(json.dumps(configuration, indent=2))
  print('SUCCESS')

## Commands that require open PASTA database, but not specific project
else:
  try:
    # open database
    if args.database=='':
      with open(os.path.expanduser('~')+'/.pasta.json','r') as f:
        config = json.load(f)
        args.database = config['-defaultLocal']
    success = True
    initViews, initConfig = False, True
    if args.command=='test':
      initViews, initConfig = True, False
    be = Pasta(args.database, initViews=initViews, initConfig=initConfig)

    # depending on commands
    if args.command=='test':
      print('database server:',be.db.db.client.server_url)
      print('configName:',be.configName)
      print('database name:',be.db.db.database_name)
      if be.db.getDoc('-ontology-')['_id'] == '-ontology-':
        print('Ontology exists on server')
      else:
        print('Ontology does NOT exist on server')
      print('local directory:',be.basePath)
      print('software directory:',be.softwarePath)
      os.chdir(be.softwarePath)
      cmd = ['git','show','-s','--format=%ci']
      output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
      print('software version:',' '.join(output.stdout.decode('utf-8').split()[0:2]))

    elif args.command=='updatePASTA':
      os.chdir(be.softwarePath)
      cmd = ['git','pull']
      output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
      print(output.stdout.decode('utf-8'))
      cmd = ['pip3','install','-r','requirements.txt','--disable-pip-version-check']
      output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
      print(output.stdout.decode('utf-8'))

    elif args.command=='verifyDB':
      output = be.checkDB(verbose=False)
      print(output)
      if '**ERROR' in output:
        success = False

    elif args.command=='syncLR':
      success = be.replicateDB()

    elif args.command=='syncRL':
      print('syncRL not implemented yet')

    elif args.command=='print':
      print(be.output(args.label,True))

    elif args.command=='saveBackup':   #save to backup file.zip
      be.backup('backup')

    elif args.command=='loadBackup':   #load from backup file.zip
      be.backup('restore')

    elif args.command=='extractorTest':
      if args.path and not args.docID:
        path = args.path
      elif args.docID and not args.path:
        doc = dict(be.getDoc(args.docID))
        path = doc['branch'][0]['path']
      else:
        print("SOMETHING STRANGE",args.path,args.docID)
      if args.content is None:
        doc = {'type':['measurement']}
      else:
        doc = {'type':args.content.split('/')}
      be.getMeasurement(path,"empty_md5sum",doc,extractorTest=True)
      if len(doc['type'])>1:
        print("SUCCESS")
      else:
        print("**ERROR**")
        success = False

    elif args.command=='redo':
      doc = dict(be.getDoc(args.docID))
      doc['type'] = args.content.split('/')
      be.getMeasurement(doc['branch'][0]['path'], doc['shasum'], doc, extractorRedo=True)  #any path is good since the file is the same everywhere; doc-changed by reference
      be.db.updateDoc({'image':doc['image']},args.docID)
      success=True

    elif args.command=='createDoc':
      content = args.content.replace("'",'"')
      doc = json.loads(content)
      docType = doc['docType']
      del doc['docType']
      if len(args.docID)>1:
        be.changeHierarchy(args.docID)
      be.addData(docType,doc)

    else:

      ## Commands that require open database and open project
      if args.docID!='':
        be.changeHierarchy(args.docID)

      if args.command=='scanHierarchy':
        be.scanTree()                 #there can not be a callback function

      elif args.command=='saveHierarchy':
        content = args.content.replace('\\n','\n')
        if content[0]=='"' and content[-1]=='"':
          content = content[1:-1]
        elif content[0]=='"' or content[-1]=='"':
          print('SOMETHING STRANGE occurs with content string')
        ## FOR DEBUGGING OF CONTENT STRING
        # print('---- Ensure beginning & end are correct ----')
        # print(content)
        # print('---- Ensure beginning & end are correct ----')
        success = be.setEditString(content)

      elif args.command=='hierarchy':
        print(be.outputHierarchy(True,True))

      ## Default case for all: unknown
      else:
        print("Command does not exist:",args.command)
        be.exit()
        raise NameError('Wrong command: '+args.command)

    be.exit()
    if success:
      print('SUCCESS')
    else:
      print('**ERROR**')
  except:
    print(traceback.format_exc())
    sys.exit(1)
