import sys, json
import requests, secrets
from PIL import Image, ImageDraw, ImageFont

def createUserDatabase(url, admin, password, userName):
  headers = requests.structures.CaseInsensitiveDict()
  headers["Content-Type"] = "application/json"
  auth = requests.auth.HTTPBasicAuth(admin, password)
  userPW = secrets.token_urlsafe(13)
  userDB = userName.replace('.','_')

  # create database
  resp = requests.put(url+'/'+userDB, headers=headers, auth=auth)
  print('Step 1 - status code:', resp.status_code)
  if not resp.ok:
    print("**ERROR 1: put not successful",resp.reason)
    return

  # create user
  data = {"docs":[{"_id":"org.couchdb.user:"+userName,"name": userName,"password":userPW,
    "roles":[userDB+"-W"], "type": "user", "orcid": ""}]}
  data = json.dumps(data)
  resp = requests.post(url+'/_users/_bulk_docs', headers=headers, auth=auth, data=data)
  print('Step 2 - status code:', resp.status_code)
  if not resp.ok:
    print("**ERROR 2: post not successful",resp.reason)
    return

  # create _security in database
  data = {"admins": {"names":[],"roles":[userDB+"-W"]},
          "members":{"names":[],"roles":[userDB+"-R"]}}
  data = json.dumps(data)
  resp = requests.put(url+'/'+userDB+'/_security', headers=headers, auth=auth, data=data)
  print('Step 3 - status code:', resp.status_code)
  if not resp.ok:
    print("**ERROR 3: post not successful",resp.reason)
    return

  # create _design/authentication in database
  data = {"validate_doc_update": "function(newDoc, oldDoc, userCtx) {"+\
    "if (userCtx.roles.indexOf('"+userDB+"-W')!==-1){return;} "+\
    "else {throw({unauthorized:'Only Writers (W) may edit the database'});}}"}
  data = json.dumps(data)
  resp = requests.put(url+'/'+userDB+'/_security', headers=headers, auth=auth, data=data)
  print('Step 4 - status code:', resp.status_code)
  if not resp.ok:
    print("**ERROR 4: post not successful",resp.reason)
    return

  print('SUCCESS: Server interaction')
  #create image
  img = Image. new('RGB', (500, 500), color = (0, 65, 118))
  d = ImageDraw. Draw(img)
  font = ImageFont.truetype("arial.ttf", 24)
  d.text((30, 30),  "configuration name: remote", fill=(240,240,240), font=font)
  d.text((30, 70),  "user-name: "+userName, fill=(240,240,240), font=font)
  d.text((30,110),  "password: " +userPW,   fill=(240,240,240), font=font)
  d.text((30,150),  "database: " +userDB,   fill=(240,240,240), font=font)
  d.text((30,150),  "Remote configuration", fill=(240,240,240), font=font)
  d.text((30,150),  "Server:   " +url, fill=(240,240,240), font=font)
  img.save(userDB+'.png')
  return


if __name__ ==  '__main__':
  ## URL
  url = input('Enter the URL without http and without port: ')
  if len(url)<2:
    print('* No legit URL entered: exit')
    sys.exit(1)
  url = 'http://'+url+':5984'
  ## User-name, password
  administrator = input('Enter the administrator username: ')
  password =      input('Enter the administrator password: ')
  userName =      input('Enter the user-name, e.g. m.miller: ')
  if len(userName)<2:
    print('* No legit user-name was entered: exit')
    sys.exit(1)
  ## USE DATA
  createUserDatabase(url, administrator, password, userName)
