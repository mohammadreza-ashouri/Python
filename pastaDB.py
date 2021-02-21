#!/usr/bin/python3
""" Main function when command-line commands used

Called by user or reactElectron frontend. Keep it simple: only functions that
are required by frontend. Otherwise, make only temporary changes
"""
import os, json, sys, subprocess
import argparse, traceback
from backend import Pasta
from miscTools import upOut

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
''')
argparser.add_argument('command', help='help, test, updatePASTA, verifyDB, saveBackup, loadBackup, print, scanHierarchy, saveHierarchy, addDoc, hierarchy, newDB, extractorTest')
argparser.add_argument('-i','--docID',   help='docID of project', default='')
argparser.add_argument('-c','--content', help='content to save/store/extractorTest', default=None)
argparser.add_argument('-l','--label',   help='label used for printing', default='Projects')
argparser.add_argument('-p','--path',    help='path for extractor test', default='')
argparser.add_argument('-d','--database',help='name of database configuration', default='') #required for be = Pasta(args.database)
args = argparser.parse_args()
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
else:
  #other commands require open PASTA database
  try:
    if args.database=='':
      with open(os.path.expanduser('~')+'/.pasta.json','r') as f:
        config = json.load(f)
        args.database = config['-defaultLocal']
    success = True
    initViews, initConfig = False, True
    if args.command=='test':
      initViews, initConfig = True, False
    be = Pasta(args.database, initViews=initViews, initConfig=initConfig)
    # depending on choices
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
      if args.content is None:
        doc = {'type':['measurement', '']}
      else:
        doc = {'type':['measurement', '', args.content]}
      be.getMeasurement(args.path,"empty_md5sum",doc,extractorTest=True)
      if len(doc['type'])>1:
        print("SUCCESS")
      else:
        print("**ERROR**")
    elif args.command=='addDoc':
      content = args.content.replace("'",'"')
      doc = json.loads(content)
      docType = doc['docType']
      del doc['docType']
      if len(args.docID)>1:
        be.changeHierarchy(args.docID)
      be.addData(docType,doc)
    else:
      #all commands that require an open project
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
        print('---- Ensure beginning & end are correct ----')
        print(content)
        print('---- Ensure beginning & end are correct ----')
        success = be.setEditString(content)
      elif args.command=='hierarchy':
        print(be.outputHierarchy(True,True))
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
