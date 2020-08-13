#!/usr/bin/python3
""" Main function when command-line commands used
"""
import argparse, textwrap, traceback, sys
from backend import JamDB

sys.path.append('/home/sbrinckm/FZJ/SourceCode/Micromechanics/src')  #allow debugging in vscode which strips the python-path
argparser = argparse.ArgumentParser(usage='''
jamDB.py <command> <item>

Possible commands are:
    print: print overview
        item can be 'Projects', 'Samples', 'Measurements', 'Procedures'
    clean, scan, produce, compare, hierarchy:
        item is documentID. To be identified by printing Project
    cleanAll: cleans all directories: item not needed
    newDB: add/update database configuration. item is e.g.
        '{"test":{"user":"Peter","password":"Parker",...}}'
    filterTest: test the filter for this file
        item is the path to file from base folder
''')
argparser.add_argument('command', help='print, clean, scan, produce, compare, hierarchy, newDB')
argparser.add_argument('item',    help="'Projects', 'Samples', 'Measurements', 'Procedures', 'documentID'")
argparser.add_argument('-db','--database', help='name of database configuration') #required for be = JamDB(args.database)
argparser.add_argument('--options', help='Options for filterTest')
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
    if args.command=='print':
      print(be.output(args.item,True))
    elif args.command=='backup':
      be.backup(args.item)
    elif args.command=='filterTest':
      if args.options is None:
        be.getMeasurement(args.item,"empty_md5sum",{'type':['measurement', '']},show=True)
      else:
        be.getMeasurement(args.item,"empty_md5sum",{'type':['measurement', '', args.options]},show=True)
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
  except:
    print(traceback.format_exc())
    print("HELP:")
    argparser.print_help()
    exit(1)
