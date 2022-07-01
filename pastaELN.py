#!/usr/bin/python3
""" Main function when command-line commands used

Called by user or reactElectron frontend. Keep it simple: only functions that
are required by frontend. Otherwise, make only temporary changes
"""
import json, sys, argparse, traceback
from pathlib import Path
from subprocess import run, PIPE, STDOUT
import urllib.request
from backend import Pasta
from miscTools import upOut, upIn, getExtractorConfig, printQRcodeSticker, checkConfiguration


def commands(getDocu, args):
  """
  Main function

  Args:
    getDocu (bool): True=return documentation string; False=use arguments
    args (argparse.Namespace): arguments supplied by user / frontend

  Returns:
    string: documentation or empty string
  """
  doc = ''
  pathConfig = Path.home().joinpath('.pastaELN.json')

  ##################################################
  ## general things that do not require open database / change configuration file
  if getDocu:
    doc += '  help: help information\n'
    doc += '    example: pastaELN.py help\n'
  elif args.command=='help':
    print("HELP:")
    argparser.print_help()
    return ''

  doc += '\n-- Configuration file commands --\n'
  if getDocu:
    doc += '  verifyConfiguration: verify configuration file\n'
    doc += '    example: pastaELN.py verifyConfiguration\n'
    doc += '    example: pastaELN.py verifyConfigurationDev (repair function)\n'
  elif args.command.startswith('verifyConfiguration'):
    repair = args.command=='verifyConfigurationDev'
    output = checkConfiguration(repair=repair)
    print(output)
    if not '**ERROR' in output:
      print('SUCCESS')
    return ''

  if getDocu:
    doc += '  newDB: add/update database configuration. item is e.g.\n'
    doc += '    {"test":{"user":"Peter","password":"Parker",...}}\n'
  elif args.command=='newDB':
    #use new database configuration and store in local-config file
    newDB = json.loads(args.item)
    label = list(newDB.keys()).pop()
    with open(pathConfig,'r', encoding='utf-8') as f:
      configuration = json.load(f)
    configuration[label] = newDB[label]
    with open(pathConfig,'w', encoding='utf-8') as f:
      f.write(json.dumps(configuration, indent=2))
    return ''

  if getDocu:
    doc += '  extractorScan: get list of all extractors and save into .pastaELN.json\n'
    doc += '    example: pastaELN.py extractorScan\n'
  elif args.command=='extractorScan':
    with open(pathConfig,'r', encoding='utf-8') as f:
      configuration = json.load(f)
      pathToExtractors = Path(__file__).parent.joinpath('extractors') \
        if 'extractorDir' not in configuration \
        else configuration['extractorDir']
    extractors = getExtractorConfig(pathToExtractors)
    extractors = [extractors[i]['plots'] for i in extractors if len(extractors[i]['plots'])>0 ] #remove empty entries
    extractors = [i for sublist in extractors for i in sublist]   #flatten list
    extractors = {'/'.join(i):j for (i,j) in extractors}
    print('Found extractors',extractors)
    with open(pathConfig,'r', encoding='utf-8') as f:
      configuration = json.load(f)
    configuration['extractors'] = extractors
    with open(pathConfig,'w', encoding='utf-8') as f:
      f.write(json.dumps(configuration, indent=2))
    print('SUCCESS')
    return ''

  if not getDocu and args.command=='up':
    print('up:',upOut(args.docID))
    return ''

  if getDocu:
    doc += '  scramble: scramble the password and user name in configuration file\n'
    doc += '    example: pastaELN.py scramble\n'
  elif args.command=='scramble':
    with open(pathConfig,'r', encoding='utf-8') as f:
      configuration = json.load(f)
    configBackup  = dict(configuration)
    links = configuration['links']
    changed = False
    for link,site in [(i,j) for i in links.keys() for j in ['local','remote']]:
      if 'user' in links[link][site] and 'password' in links[link][site]:
        links[link][site]['cred'] = upIn(links[link][site]['user']+':'+links[link][site]['password'])
        del links[link][site]['user']
        del links[link][site]['password']
        changed = True
    if changed:
      with open(Path.home().joinpath('.pastaELN_BAK.json'),'w', encoding='utf-8') as f:
        f.write(json.dumps(configBackup,indent=2))
      with open(pathConfig,'w', encoding='utf-8') as f:
        f.write(json.dumps(configuration,indent=2))
    return ''

  if getDocu:
    doc += '  decipher: decipher encrypted string\n'
    doc += '    content: string\n'
  elif args.command=='decipher':
    from serverActions import passwordDecrypt
    print(passwordDecrypt(args.content).decode())
    print('SUCCESS')


  ##################################################
  ## Commands that require open PASTA database, but not specific project
  doc += '\n-- Commands that interact with backend --\n'
  try:
    # use configuration file
    if not getDocu:
      with open(pathConfig,'r', encoding='utf-8') as f:
        config = json.load(f)
      if args.database=='':
        args.database = config['default']

    initViews, initConfig, resetOntology = False, True, False
    if getDocu:
      doc += '  test: test PASTA setup\n'
      doc += '    example: pastaELN.py test -d instruments\n'
    elif args.command.startswith('test'):
      #PART 1 of test: precede with configuration test
      initViews, initConfig = True, True
      if args.command=='testDev':
        resetOntology = True
      output = checkConfiguration(repair=False)  #verify configuration file .pastaELN.py
      print(output)
      if 'ERROR' in output:
        return ''
      # local and remote server test
      urls = ['http://127.0.0.1:5984']
      if config['links'][args.database]['remote']!={}:
        urls.append(config['links'][args.database]['remote']['url'])
      for url in urls:
        try:
          with urllib.request.urlopen(url) as package:
            contents = package.read()
            if json.loads(contents)['couchdb'] == 'Welcome':
              print('CouchDB server',url,'is working: username and password test upcoming')
        except:
          print('**ERROR pma01: CouchDB server not working |',url)
          if url=='http://127.0.0.1:5984':
            raise NameError('**ERROR pma01a: Wrong local server.') from None

    #open backend
    if not getDocu:
      try:
        be = Pasta(linkDefault=args.database, initViews=initViews, initConfig=initConfig,
                  resetOntology=resetOntology)
      except:
        print('**ERROR pma20: backend could not be started.\n'+traceback.format_exc()+'\n\n')
        return ''

    if not getDocu and args.command.startswith('test') and be:
      #PART 2 of test: main test
      print('database server:',be.db.db.client.server_url)
      print('default link:',be.confLinkName)
      print('database name:',be.db.db.database_name)
      designDocuments = be.db.db.design_documents()
      print('Design documents')
      for item in designDocuments:
        numViews = len(item['doc']['views']) if 'views' in item['doc'] else 0
        print('  ',item['id'], '   Num. of views:', numViews )
      try:
        doc = be.db.getDoc('-ontology-')
        print('Ontology exists on server')
      except:
        print('**ERROR pma02: Ontology does NOT exist on server')
      print('local directory:',be.basePath)
      print('software directory:',be.softwarePath)
      output = run(['git','tag'], cwd=be.softwarePath, stdout=PIPE, stderr=STDOUT, check=True)
      print('software version: '+output.stdout.decode('utf-8').split('\n')[-2])
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  verifyDB: test PASTA database\n'
      doc += '    example: pastaELN.py verifyDB\n'
      doc += '    example: pastaELN.py verifyDBdev (repair function)\n'
    elif args.command.startswith('verifyDB'):
      repair = args.command=='verifyDBdev'
      output = be.checkDB(verbose=False, repair=repair)
      print(output)
      be.exit()
      if not '**ERROR' in output:
        print('SUCCESS')
      return ''

    if getDocu:
      doc += '  syncLR / syncRL: synchronize with / from remote server\n'
      doc += '    example: pastaELN.py syncLR\n'
    elif args.command=='syncLR':
      success = be.replicateDB()
      be.exit()
      if success:
        print('SUCCESS')
      return ''
    elif args.command=='syncRL':
      be.exit()
      print('**ERROR pma03: syncRL not implemented yet')
      return ''

    if getDocu:
      doc += '  print: print overview\n'
      doc += "    label: possible docLabels 'Projects', 'Samples', 'Measurements', 'Procedures'\n"
      doc += "    example: pastaELN.py print -d instruments -l instrument\n"
    elif args.command=='print':
      print(be.output(args.label,True))
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  printQRCodes: print qr-codes\n'
      doc += "    content: list of qrCodes and text\n"
      doc += "    note: requires set -qrPrinter in pasta.json\n"
      doc += '    example: pastaELN.py printQRCodes -c \'[["my name","Sample 1"], ["","Oven 450C"]]\'\n'
    elif args.command=='printQRCodes':
      content = args.content.replace('\\n','\n')
      if content[0]=='"' and content[-1]=='"':
        content = content[1:-1]
      content = json.loads(content)
      printQRcodeSticker(content, config['-qrPrinter']['page'], config['-qrPrinter']['printer'])
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  saveBackup,loadBackup: save to file.zip / load from file.zip\n'
      doc += '    - docId is optional as it reduces the scope of the backup\n'
      doc += '    - database is optional as otherwise the default is used\n'
      doc += '    example: pastaELN.py saveBackup -d instruments\n'
      doc += '    example: pastaELN.py saveBackup -i x-76b0995cf655bcd487ccbdd8f9c68e1b\n'
    elif args.command=='saveBackup':   #save to backup file.zip
      be.backup('backup', None, args.docID)
      be.exit()
      print('SUCCESS')
      return ''
    elif args.command=='loadBackup':   #load from backup file.zip
      be.backup('restore')
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  importXLS: import first sheet of excel file into database\n'
      doc += '    before: ensure database configuration and project exist\n'
      doc += '    example: pastaELN.py importXLS -d instruments -i x-123456 -c "~/path/to.xls" -l instrument\n'
      doc += '    -l is the document type\n'
      doc += '    afterwards: adopt ontology (views are automatically generated)\n'
    elif args.command=='importXLS':
      import pandas as pd
      from commonTools import commonTools as cT  #not globally imported since confuses translation
      if args.docID!='':
        be.changeHierarchy(args.docID)
      data = pd.read_excel(args.content, sheet_name=0).fillna('')
      for _, row in data.iterrows():
        doc = dict((k.lower(), v) for k, v in row.items())
        be.addData(args.label, doc )
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  createDoc: add document to database\n'
      doc += '    content is required as json-string\n'
      doc += "    example: pastaELN.py createDoc --content \"{'-name':'Instruments','docType':'project'}\"\n"
    elif args.command=='createDoc':
      from urllib import parse
      content = parse.unquote(args.content)
      doc = json.loads(content)
      docType = doc['docType']
      del doc['docType']
      if len(args.docID)>1 and args.docID!='none':
        be.changeHierarchy(args.docID)
      be.addData(docType,doc)
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  redo: recreate thumbnail\n'
      doc += '    example: pastaELN.py redo -i m-1234567890abcdefghijklmnopqrstuv -c type/test/subtest\n'
    elif args.command=='redo':
      doc = dict(be.getDoc(args.docID))
      doc['-type'] = args.content.split('/')
      be.useExtractors(doc['-branch'][0]['path'], doc['shasum'], doc, extractorRedo=True)  #any path is good since the file is the same everywhere; doc-changed by reference
      if len(doc['-type'])>1 and len(doc['image'])>1:
        be.db.updateDoc({'image':doc['image'], '-type':doc['-type']},args.docID)
        print('SUCCESS')
      else:
        print('**ERROR pma06: error after redo-extraction')
      be.exit()
      return ''

    if getDocu:
      doc += '  history: get history for docTypes\n'
      doc += '    example: pastaELN.py history\n'
    elif args.command=='history':
      print(be.db.historyDB())
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  updatePASTA: update software version\n'
      doc += '    example: pastaELN.py updatePASTA\n'
    elif args.command=='updatePASTA':
      #update desktop incl. Python backend
      softwarePath = Path(be.softwarePath)
      run(['git','pull'], cwd=softwarePath.parent, stdout=PIPE, stderr=STDOUT, check=True)
      # print(text.stdout.decode('utf-8')) #temporarily don't print
      #ensure requirements are fulfilled
      run(['git','pull'], cwd=softwarePath, stdout=PIPE, stderr=STDOUT, check=True)
      # print(text.stdout.decode('utf-8')) #temporarily don't print
      cmd = ['pip3','install','-r','requirements.txt','--disable-pip-version-check']
      run(cmd, cwd=softwarePath, stdout=PIPE, stderr=STDOUT, check=True)
      # print(text.stdout.decode('utf-8')) #temporarily don't print
      be.exit()
      print('SUCCESS')
      return ''

    ##################################################
    ## Commands that require open database and open project
    doc += '\n-- Commands that interact with a special project --\n'
    if not getDocu and args.docID!='':
      be.changeHierarchy(args.docID)

    if getDocu:
      doc += '  scanHierarchy: scan project with docID\n'
      doc += '    example: pastaELN.py scanHierarchy -i ....\n'
    elif args.command=='scanHierarchy':
      be.scanTree()
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  saveHierarchy: save hierarchy to database\n'
      doc += '    example: pastaELN.py saveHierarchy -c "{...}" -i x-1234567890abc'
    elif args.command=='saveHierarchy':
      content = args.content.replace('\\n','\n')
      if content[0]=="'" and content[-1]=="'":
        content = content[1:-1]
      elif content[0]=="'" or content[-1]=="'":
        print('**ERROR pma07: something strange occurs with content string')
      ## FOR DEBUGGING OF CONTENT STRING
      # print('---- Ensure beginning & end are correct ----')
      # print(content)
      # print('---- Ensure beginning & end are correct ----')
      success = be.setEditString(content)
      be.exit()
      print('SUCCESS')
      return ''

    if getDocu:
      doc += '  hierarchy: print document hierarchy\n'
      doc += '    example: pastaELN.py hierarchy -i x-1234567890abc'
    elif args.command=='hierarchy':
      print(be.outputHierarchy(True,True))
      be.exit()
      print('SUCCESS')
      return ''

  except:
    print("**ERROR pma10: exception thrown during pastaELN.py"+traceback.format_exc()+"\n")
    raise

  # only can be reached if getDocu
  return doc

###################
## MAIN FUNCTION ##
if __name__=='__main__':
  usage = "pastaELN.py <command> [-i docID] [-c content] [-l labels] [-d database]\n\n"
  usage+= "Possible commands are:\n"
  usage+= commands(True, None)
  argparser = argparse.ArgumentParser(usage=usage)
  argparser.add_argument('command', help='see above...')
  argparser.add_argument('-i','--docID',   help='docID of project; always a long alpha-numeric code', default='')
  argparser.add_argument('-c','--content', help='content to save/store', default=None)
  argparser.add_argument('-l','--label',   help='label used for printing', default='x0')
  argparser.add_argument('-d','--database',help='name of database configuration', default='') #required for be = Pasta(args.database)
  arguments = argparser.parse_args()
  commands(False, arguments)
