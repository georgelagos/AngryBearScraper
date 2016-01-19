import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
import urllib
import urllib2
#from urllib import request
#import urllib.error
import os
import re
from PIL import Image

gamelist = Element('gameList')
#platformNum = 18
#gameDir = 'Roms'
#savePath = '500px_Imgs'
maxWidth = 500

# platform ids from thegamesdb.net
platformDict = { 'NES': 7, 'SNES': 6, 'Genesis': 18, 'PlaystationX': 10, 'PSP': 13 }

destGameDirs = { 'NES': '/home/pi/RetroPie/roms/nes/',
                 'SNES': '/home/pi/RetroPie/roms/snes/',
                 'Genesis': '/home/pi/RetroPie/roms/megadrive/',
                 'PlaystationX': '/home/pi/RetroPie/roms/psx',
                 'PSP': '/home/pi/RetroPie/roms/snes/' }

def num_to_plat(key):
    switcher = {
        1: "NES",
        2: "SNES",
        3: "Genesis",
        4: "PlaystationX",
        5: "PSP",
    }
    return switcher.get(key, "None")

print ('Emulation Station Content Scraper')
print ('[1] NES')
print ('[2] SNES')
print ('[3] Sega Genesis / Megadrive')
print ('[4] Playstation X / PS 1-2')
print ('[5] Sony PSP')

platformInput = input('Please choose a platform : ')

platformNum = platformDict[num_to_plat(int(platformInput))]

gameDir = destGameDirs[num_to_plat(int(platformInput))]

print('Searching for ' + num_to_plat(int(platformInput)) + ' games ...')


xmlUrl = 'http://thegamesdb.net/api/GetPlatformGames.php?platform='+str(platformNum)
#print(xmlUrl)

req = urllib2.Request(xmlUrl,headers={'User-Agent': 'Mozilla/5.0'})
print(req)
source = urllib2.urlopen(req)

tree = ET.parse(source)
root = tree.getroot()

for files in os.listdir(gameDir):
    gameTitle = re.sub(r'\[.*?\]|\(.*?\)', '', files)
    gameTitle = re.sub(r'\s\-\s', ' ', gameTitle)
    gameTitle = re.sub(r'&', '&amp;', gameTitle)
    gameTitle = re.sub(r'[!:]', '', gameTitle)
    gameTitle = gameTitle.rpartition('.')[0]
    gameTitle = gameTitle.rsplit(',')[0]
    gameTitle = gameTitle.strip()
    gameTitle = gameTitle.lower()
    print('Filename: ', files)

    numResult = 0
    resultsList = []
       
    for games in root.findall('Game'):
        
        gamesDbTitle = games.find ('GameTitle').text
        xmlTitle = games.find ('GameTitle').text
        xmlTitle = re.sub(r'\s\-\s', ' ', xmlTitle)
        xmlTitle = re.sub(r'&', '&amp;', xmlTitle)
        xmlTitle = re.sub(r'[!:]', '', xmlTitle)
        xmlTitle = xmlTitle.strip()
        xmlTitle = xmlTitle.lower()
        
        if gameTitle in xmlTitle:
            gameId = games.find('id').text
            numResult = numResult + 1
            multGameTitles =(gameId, gamesDbTitle)
            resultsList.append(multGameTitles)
            
    if numResult > 1:
        for i, v in enumerate(resultsList):
            print ('[{0}] {1}'.format(i, v[1]))

        try:    
            #print ("Number of Results:", numResult)
            choice = int(input("Select a result: "))
            gameId = resultsList[choice][0]
            print (gameId)
        except Exception:
            print('Skipping...')
            continue
        
    elif numResult == 0:
        print("Game not found.")
        continue
    else:
        print ("Game found.")

    try:
        # Get game metadata
        getGameXmlUrl = "http://thegamesdb.net/api/GetGame.php?id="+str(gameId)
        req = urllib2.Request(getGameXmlUrl,headers={'User-Agent': 'Mozilla/5.0'})
        getGameXml = urllib2.urlopen(req)
        gameTree = ET.parse(getGameXml)
        gameRoot = gameTree.getroot()

        #Get boxart
        print('Downloading boxart ...')

        # add exception for null text. no image available.
        imageUrlPath = gameRoot.find("Game/Images/boxart[@side='front']").text
        
        fileName = files.rpartition('.')[0]
        extension = imageUrlPath.rpartition('.')[2]
        imgFile = fileName+'.'+extension
        

        relImgPath = os.path.join(gameDir,imgFile)
        f = open(relImgPath,'wb')
        req = urllib2.Request('http://thegamesdb.net/banners/'+imageUrlPath,headers={'User-Agent': 'Mozilla/5.0'})
        f.write(urllib2.urlopen(req).read())
        f.close()
        
        #resize box art
        img = Image.open(relImgPath)
        height = int((float(img.size[1])*float(maxWidth/float(img.size[0]))))
        newSize = maxWidth, height
        img = img.resize(newSize, resample=0)
        
        #print (img.size)
        print (newSize)
        img.save(relImgPath)
    except Exception as Err:
        print('An unexpected error has occured: ' + str(Err))
        continue

    # Form new XML

    try:
        game = SubElement(gamelist, 'game')

        path = SubElement(game, 'path')
        name = SubElement(game, 'name')
        desc = SubElement(game, 'desc')
        image = SubElement(game, 'image')
        
        path.text = gameDir + files
        name.text = gameRoot.find('Game/GameTitle').text
        desc.text = gameRoot.find('Game/Overview').text
        image.text = gameDir + imgFile
    except Exception as Err:
        print('An unexpected error has occured: ' + str(Err))
        continue

# Write XML
#ET.dump(gamelist)
gameListRoot = ET.ElementTree(gamelist)
gameListRoot.write(gameDir + 'gamelist.xml')
