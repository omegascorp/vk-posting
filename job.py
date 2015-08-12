import urllib
import urllib.parse
import json
import requests
import os
import logging
import random
import time
import sys

def request(url, data):
    res = requests.get(url + '?' + urllib.parse.urlencode(data))
    return json.loads(res.content.decode())
def upload(url, path, photo):
    f = open(path+photo, 'rb')
    fileName = '1.'+parseExtension(photo)
    res = requests.post(url, files={'photo': ('1.'+fileName, f)})
    f.close()
    return json.loads(res.content.decode())
def parseTags(fileName):
    start = fileName.find('#');
    end = fileName.rfind('.');
    if(start != -1 and end != -1):
        return fileName[start:end]
    return ''
def parseText(fileName):
    start = fileName.find('!');
    sharp = fileName.find('#');
    end = fileName.rfind('.');
    text = ''
    if(start != -1 and sharp != -1):
        text = fileName[start+1:sharp]
    elif(start != -1 and end != -1):
        text = fileName[start+1:end]
    text = text.replace('|', '/');
    return text
def parseExtension(fileName):
    start = fileName.rfind('.');
    if(start != -1):
        return fileName[start+1:]
    return ''
def getUploadServer():
    response = request('https://api.vk.com/method/photos.getWallUploadServer', {
        'gid': config['groupId'],
        'access_token': config['accessToken'],
        'v': '5.12'
    })
    logging.info(response)
    return response
def savePhoto(server, photo, responseHash):
    response = request('https://api.vk.com/method/photos.saveWallPhoto', {
        'server': server,
        'photo': photo,
        'hash': responseHash,
        'gid': config['groupId'],
        'access_token': config['accessToken'],
        'v': '5.12'
    })
    logging.info(response)
    return response
def savePost(photoId, text, lastPublishDate):
    response = request('https://api.vk.com/method/wall.post', {
        'owner_id': '-' + config['groupId'],
        'attachments': 'photo' + config['userId'] + '_' + str(photoId),
        'from_group': 1,
        'access_token': config['accessToken'],
        'message': text,
        'publish_date': lastPublishDate,
        'v': '5.12'
    })
    logging.info(response)

def uploadRandomImage(path):
    imagesPath = path + 'images/'
    images = os.listdir(imagesPath)
    print(random.randint(0,len(images)-1))
    image = images[random.randint(0,len(images)-1)]

    if data['lastPublishDate'] < int(time.time()):
        data['lastPublishDate'] = int(time.time())
    else:
        data['lastPublishDate'] += 60 * 60;

    response = getUploadServer()
    uploadUrl = response['response']['upload_url']

    response = upload(uploadUrl, imagesPath, image)
    server = response['server']
    responseHash = response['hash']
    photo = response['photo']

    response = savePhoto(server, photo, responseHash)
    photoId = response['response'][0]['id']

    text = parseText(image);
    if text:
        text += '\n'
    if len(config['tags']):
        text += config['tags'] + ' ';
    text += parseTags(image)
    response = savePost(photoId, text, data['lastPublishDate'])
    os.remove(imagesPath + image)

path = os.path.dirname(os.path.abspath(__file__)) + '/'
logging.basicConfig(filename=path + 'log',level=logging.INFO)
with open(path + 'data.json') as inFile:
    data = json.load(inFile)
with open(path + 'config.json') as inFile:
    config = json.load(inFile)

runsCount = 1
if len(sys.argv) >= 2:
    runsCount = int(sys.argv[1])

for i in range(runsCount):
    uploadRandomImage(path)

with open(path + 'data.json', 'w') as outFile:
    json.dump(data, outFile)
