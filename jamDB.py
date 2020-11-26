#!/usr/bin/python3
""" Main function when command-line commands used

Called by user or reactElectron frontend

frontend calls:
  test
  scan with documentID
  save with documentID string
"""
import os, json, sys
import argparse, traceback
from backend import JamDB

argparser = argparse.ArgumentParser(usage='''
jamDB.py <command> <item>

Possible commands are:
    test: test jamDB setup
    print: print overview
        item can be 'Projects', 'Samples', 'Measurements', 'Procedures'
    clean, scan, produce, compare, hierarchy:
        item is documentID. To be identified by printing Project
    cleanAll: cleans all directories: item not needed
    newDB: add/update database configuration. item is e.g.
        '{"test":{"user":"Peter","password":"Parker",...}}'
    extractorTest: test the extractor of this file
        item is the path to file from base folder
''')
argparser.add_argument('command', help='test, print, clean, scan, produce, compare, hierarchy, newDB')
argparser.add_argument('item',    help="'Projects', 'Samples', 'Measurements', 'Procedures', 'documentID'")
argparser.add_argument('-db','--database', help='name of database configuration') #required for be = JamDB(args.database)
argparser.add_argument('--options', help='Options for extractor test')
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
else:
  #other commands require open jamDB database
  try:
    be = JamDB(args.database)
    if args.command=='test':
      print('backend was started')
    elif args.command=='print':
      print(be.output(args.item,True))
    elif args.command=='backup':
      be.backup(args.item)
    elif args.command=='extractorTest':
      if args.options is None:
        doc = {'type':['measurement', '']}
      else:
        doc = {'type':['measurement', '', args.options]}
      be.getMeasurement(args.item,"empty_md5sum",doc,extractorTest=True)
      if len(doc['type'])>1:
        print("SUCCESS")
      else:
        print("**ERROR**")
    else:
      #all commands that require an open project
      be.changeHierarchy(args.item)
      if args.command=='scan':
        be.scanTree()                 #there can not be a callback function
      elif args.command=='hierarchy':
        print(be.outputHierarchy(True,True))
      else:
        be.exit()
        raise NameError('Wrong command: '+args.command)
    be.exit()
    print('SUCCESS')
  except:
    print(traceback.format_exc())
    print("HELP:")
    argparser.print_help()
    sys.exit(1)
