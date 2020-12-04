#!/usr/bin/python3
""" Main function when command-line commands used

Called by user or reactElectron frontend

frontend calls:
  save with documentID string
"""
import os, json, sys
import argparse, traceback
from backend import JamDB

argparser = argparse.ArgumentParser(usage='''
jamDB.py <command> [-i docID] [-c content] [-l labels] [-d database] [-p path]

Possible commands are:
    help: help information
    test: test jamDB setup
    print: print overview
        item: possible docLabels 'Projects', 'Samples', 'Measurements', 'Procedures'
    scan, hierarchy: scan or print project
        item: documentID for. To be identified by printing Project
    addDoc:
      content is required as json-string
    newDB: add/update database configuration. item is e.g.
        '{"test":{"user":"Peter","password":"Parker",...}}'
    extractorTest: test the extractor of this file
        -p should be specified is the path to file from base folder
''')
argparser.add_argument('command', help='help, test, print, scan, addDoc, hierarchy, newDB, extractorTest')
argparser.add_argument('-i','--docID',   help='docID of project', default='')
argparser.add_argument('-c','--content', help='content to save/store/extractorTest', default=None)
argparser.add_argument('-l','--label',   help='label used for printing', default='Projects')
argparser.add_argument('-p','--path',    help='path for extractor test', default='')
argparser.add_argument('-d','--database',help='name of database configuration', default='') #required for be = JamDB(args.database)
args = argparser.parse_args()
if args.command=='newDB':
  #use new database configuration and store in local-config file
  newDB = json.loads(args.item)
  label = list(newDB.keys()).pop()
  with open(os.path.expanduser('~')+'/.jamDB.json','r') as f:
    configuration = json.load(f)
  configuration[label] = newDB[label]
  with open(os.path.expanduser('~')+'/.jamDB.json','w') as f:
    f.write(json.dumps(configuration, indent=2))
elif args.command=='help':
  print("HELP:")
  argparser.print_help()
else:
  #other commands require open jamDB database
  try:
    if args.database=='':
      with open(os.path.expanduser('~')+'/.jamDB.json','r') as f:
        config = json.load(f)
        args.database = config['-defaultLocal']
    be = JamDB(args.database)
    if args.command=='test':
      print('backend was started')
      print('database server:',be.db.db.client.server_url)
      print('configName:',be.configName)
      print('database name:',be.db.db.database_name)
      if be.db.getDoc('-dataDictionary-')['_id'] == '-dataDictionary-':
        print('dataDictionary exists on server')
      else:
        print('dataDictionary does NOT exist on server')
      print('local directory:',be.basePath)
      print('software directory:',be.softwarePath)
    elif args.command=='print':
      print(be.output(args.label,True))
    elif args.command=='backup':
      be.backup()
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
      doc = json.loads(args.content)
      docType = doc['docType']
      del doc['docType']
      print('addDoc',docType,doc)
      be.addData(docType,doc)
    else:
      #all commands that require an open project
      be.changeHierarchy(args.docID)
      if args.command=='scan':
        be.scanTree()                 #there can not be a callback function
      elif args.command=='save':
        print(args.content[1:-1])
        print('>> Ensure that the beginning end are correct <<')
        be.setEditString(args.content[1:-1])
      elif args.command=='hierarchy':
        print(be.outputHierarchy(True,True))
      else:
        be.exit()
        raise NameError('Wrong command: '+args.command)
    be.exit()
    print('SUCCESS')
  except:
    print(traceback.format_exc())
    sys.exit(1)
