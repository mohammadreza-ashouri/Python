import json, re
import base64, io
from PIL import Image


def jsonValidator(data):
  """
  for debugging, test if valid json object

  Args: 
     data: string to test
  """
  try:
    json.loads(json.dumps(data) )
    return True
  except ValueError as error:
    print("**ERROR** invalid json: %s" % error)
    return False


def string2TagFieldComment(comment):
  """
  extract tags, fields and comments from string

  Args:
     comment: input string
  """
  reply = {}
  tags = re.findall("#[\S]+",comment)
  for tag in tags:
    comment = comment.replace(tag,"")
  reply["tags"] = [tag[1:] for tag in tags]
  fields = re.findall(":[\S]+:[\S]+:",comment)
  for field in fields:
    comment = comment.replace(field,"")
    _, key, value, _ = field.split(":")
    try:
      value = float(value)
    except:
      pass
    reply[key] = value
  reply["comment"] = comment.strip().replace("  "," ")
  return reply


def camelCase(text):
  """
  Convert string to camelCase string

  Args:
     text: input text
  """
  camelCase = ''.join(x for x in text.title() if not x.isspace())
  return camelCase


def imageToString(url):
  """
  convert png file to b64-string

  future: test if jpeg and png strings are the same
  do I need to save jpeg, png as marker in list ['png',64byte]
  https://stackoverflow.com/questions/16065694/is-it-possible-to-create-encoded-base64-url-from-image-object

  Args:
     url: path to image
  """
  encoded = base64.b64encode(open(url,'rb').read())
  aString = encoded.decode()
  return aString


def stringToImage(aString, show=True):
  """
  convert a b64-string to png file

  Args:
     aString: 64byte string of image
     show: show image
  """
  imgdata = base64.b64decode(aString)
  image = Image.open(io.BytesIO(imgdata))
  if show:
    image.show()
  return image