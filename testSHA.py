from miscTools import generic_hash

fileName = "/home/sbrinckm/temporary_test/TestProject2/Zeiss.tif"
result = generic_hash(fileName)
print(result,fileName)

fileName = "/home/sbrinckm/temporary_test/TestProject2/.git/annex/objects/pX/5m/MD5E-s840068--b30620513e355f1b31ad703e8638f972.tif/MD5E-s840068--b30620513e355f1b31ad703e8638f972.tif"
result = generic_hash(fileName)
print(result,fileName)

fileName = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png"
result = generic_hash(fileName)
print(result,fileName)

fileName = "320px-Google_2015_logo.svg.png"
result = generic_hash(fileName)
print(result,fileName)

"""
from hashlib import sha1
from urllib import request
path = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png"
req = request.urlopen(path)
"""

