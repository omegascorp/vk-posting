import urllib
import urllib.parse
import json
import requests
import os
import os.path
import logging
import random
import time
import sys
import shutil

def request(url, data):
    res = requests.get(url + '?' + urllib.parse.urlencode(data))
    return json.loads(res.content.decode())
def uploadPhoto(url, path, photo):
    f = open(path+photo, 'rb')
    fileName = '1.'+parseExtension(photo)
    res = requests.post(url, files={'photo': ('1.'+fileName, f)})
    f.close()
    return json.loads(res.content.decode())
def uploadAndSavePhoto(url, path, photo):
    response = uploadPhoto(url, path, photo)
    response = savePhoto(response['server'], response['photo'], response['hash'])
    return response['response'][0]['id']
def parseTags(fileName, isDir):
    start = fileName.find('#')
    if isDir:
        end = len(fileName)
    else:
        end = fileName.rfind('.')
    if(start != -1 and end != -1):
        return fileName[start:end]
    return ''
def parseText(fileName, isDir):
    start = fileName.find('!')
    sharp = fileName.find('#')
    if isDir:
        end = len(fileName)
    else:
        end = fileName.rfind('.')
    text = ''
    if(start != -1 and sharp != -1):
        text = fileName[start+1:sharp]
    elif(start != -1 and end != -1):
        text = fileName[start+1:end]
    text = text.replace('|', '/')
    return text
def parseExtension(fileName):
    start = fileName.rfind('.')
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
def savePost(photoIds, text, lastPublishDate):
    attachments = '';
    if isinstance(photoIds, list):
        for photoId in photoIds:
            if len(attachments):
                attachments += ',';
            attachments += 'photo' + config['userId'] + '_' + str(photoId)
    else:
        attachments += 'photo' + config['userId'] + '_' + str(photoIds)
    response = request('https://api.vk.com/method/wall.post', {
        'owner_id': '-' + config['groupId'],
        'attachments': attachments,
        'from_group': 1,
        'access_token': config['accessToken'],
        'message': text,
        'publish_date': lastPublishDate,
        'v': '5.12'
    })
    logging.info(response)

def uploadRandomPost(path):
    imagesPath = path + 'images/'
    images = os.listdir(imagesPath)
    print(random.randint(0,len(images)-1))
    image = images[random.randint(0,len(images)-1)]
    if data['lastPublishDate'] < int(time.time()):
        data['lastPublishDate'] = int(time.time()) + 600
    else:
        data['lastPublishDate'] += 60 * config['period'];

    response = getUploadServer()
    uploadUrl = response['response']['upload_url']
    isDir = os.path.isdir(imagesPath + image)

    if isDir:
        photoIds = []
        for img in os.listdir(imagesPath + image):
            photoId = uploadAndSavePhoto(uploadUrl, imagesPath + image + '/' , img)
            photoIds.append(photoId)
    else:
        photoIds = uploadAndSavePhoto(uploadUrl, imagesPath, image)

    text = parseText(image, isDir)
    if text:
        text += '\n'
    if len(config['tags']):
        text += config['tags'] + ' '
    text += parseTags(image, isDir)
    response = savePost(photoIds, text, data['lastPublishDate'])
    if isDir:
        shutil.rmtree(imagesPath + image)
    else:
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
    uploadRandomPost(path)

with open(path + 'data.json', 'w') as outFile:
    json.dump(data, outFile)
