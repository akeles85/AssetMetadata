#!/usr/local/bin/python3

from calendar import c
from email.mime import image
import glob
from math import ceil
from PIL import Image
from multiprocessing import Pool 
import time
import os
import sys
import json
import hashlib
import wave
import contextlib


class PuzzleMetadata:
    def __init__(self, type, size):
        self.type = type
        self.size = size        
        self.filesData = []
        
    def add( self, fileData ):
        self.filesData.append(fileData)
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            indent=4)          
        
        
class FileData:
    def __init__(self, type, size, checksum):
        self.type = type
        self.size = size
        self.checksum = checksum 
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            indent=4)           
        
class TextFileData(FileData):
    def __init__(self, size, checksum):
        super().__init__("txt", size, checksum)
        self.numOfUniqeWords = 0
        self.mostContainerWord = "empty"
        self.numOfContainerWord = 0
    
    def add( self, numOfUniqeWords, mostContainerWord, numOfContainerWord ):
        self.numOfUniqeWords = numOfUniqeWords
        self.numOfUniqeWords = mostContainerWord
        self.numOfUniqeWords = numOfContainerWord    
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            indent=4)   
        
class AudioData(FileData):
    def __init__(self, size, checksum, duration):
        super().__init__("wav", size, checksum)
        self.durationInSec = duration
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            indent=4)    
        
class ImageData(FileData):
    def __init__(self, size, checksum, height, width):
        super().__init__("png", size, checksum)
        self.height = height
        self.width = width
        self.colorClusters = []
        self.numOfPixesOfClusters = []
        
        
    def addCluster(self, color, numOfPixes):
        self.colorClusters.append( color )
        self.numOfPixesOfClusters.append( numOfPixes )
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            indent=4)        
    
class Point:
  def __init__(self, coordinates):
    self.coordinates = coordinates    

def obtainTextInfo( directory, files ):
        
    totalUniqueWordForFile = []
    
    puzzleMetaData = PuzzleMetadata( "Text", 0 )
    totalAssetSize = 0
            
    for currFile in files:
        fileSize = os.path.getsize(directory + currFile)
        totalAssetSize += fileSize
        md5 = hashlib.md5(open(directory + currFile,'rb').read()).hexdigest()
        fileData = TextFileData(fileSize, md5)        
        words = {}
        with open(directory+currFile) as f:
            for currLine in f:                
                for currWord in currLine.strip().split(" "):
                    if len( currWord ) == 0:
                        continue
                    if words.get(currWord) is None:
                        words[currWord] = 1 
                    else:
                        words[currWord] = words[currWord]+1 
            
        sortedWords = sorted( words, key=len, reverse=True)    
                      
        fileData.numOfUniqeWords = len(words)
                
        comparableWords = sortedWords
        containedResult = {}
        
        for currCompWord in comparableWords:
            for currWord in sortedWords:
                if len( currWord ) > len( currCompWord ):
                    continue
                
                if currWord == currCompWord:
                    continue               
                 
                i2 = 0
                for i1 in range(len(currCompWord)):
                    if currCompWord[i1] == currWord[i2]:                        
                        i2 += 1                
                    if i2 == len(currWord):                        
                        if containedResult.get(currCompWord) is None:
                            containedResult[currCompWord] = 1
                        else:
                            containedResult[currCompWord] = containedResult[currCompWord]+1                         
                        
                        comparableWords.remove( currWord )                        
                        break
                            
        sorted_containedResult = dict( sorted( containedResult.items(), key = lambda x: x[1], reverse=True ) )

        fileData.mostContainerWord = next(iter(sorted_containedResult)) 
        fileData.numOfContainerWord = sorted_containedResult[ fileData.mostContainerWord ]
                
        puzzleMetaData.add(fileData)
    
    puzzleMetaData.size = totalAssetSize                        
    
    jsonFile = open( directory + "metadata.json", "w")
    jsonFile.write(puzzleMetaData.toJSON())
    jsonFile.close()      


def audioSearcher(fname):
    
    duration = 0
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        
    fileSize = os.path.getsize(fname)
        
    md5 = hashlib.md5(open(fname,'rb').read()).hexdigest()
     
    audioData = AudioData( fileSize, md5, round(duration) )
    
    return audioData



def rgb_to_hex(rgb):
  return '#%s' % ''.join(('%02x' % p for p in rgb))

# def get_colors(points, n_colors=3):
#   clusters = KMeans(n_clusters=n_colors).fit(points)
#   clusters.sort(key=lambda c: len(c.points), reverse = True)
#   rgbs = [map(int, c.center.coordinates) for c in clusters]
#   return list(map(rgb_to_hex, rgbs))


def imageSearcher(fname):
    
    im=Image.open(fname)   
    
    pix = im.load() 
        
    fileSize = os.path.getsize(fname)
        
    md5 = hashlib.md5(open(fname,'rb').read()).hexdigest()
     
    assetData = ImageData( fileSize, md5, im.height, im.width)
    
    
    return assetData
        
def thumbnail(directory, files): 
        
    thumbSizeX, thumbSizeY = 1000, 1000
    numOfFiles = len(files)
    if numOfFiles > 9:
        numOfFiles = 9
        
    new_im = Image.new('RGB', (thumbSizeX, thumbSizeY))
    
    numOfRow = ceil(numOfFiles / 2.0)
    numOfColumn = 2
    
    if numOfFiles < 2:
        numOfColumn = 1
    
    imageXSize = thumbSizeX / numOfColumn
    imageYSize = thumbSizeY / numOfRow
            
    rowIndex = 0
    colIndex = 0
    for filename in files:         
        try:
            # Load just once, then successively scale down
            im=Image.open(filename)    
            
            minLength = min(im.width, im.height)
            im2 = im.crop((1,1,minLength,minLength))        
        
            im2.thumbnail((imageXSize,imageYSize))
            
            new_im.paste(im2, ( (int)(colIndex*imageXSize), (int)(rowIndex*imageYSize)))      
            
            colIndex = colIndex+1
            if colIndex == numOfColumn:
                colIndex = 0
                rowIndex = rowIndex + 1
                                        
        except Exception as e: 
            return e
    
    new_im.save("t-100.jpg")
    return 'OK'
 
    

n = len(sys.argv) 

#if n != 2:
#    print("Error with parameter")
#    print("Example usage: python3 test.py /path/to/puzzleDirectory")    
#    sys.exit(-1)

#inputDirectory = sys.argv[1]
inputDirectory = "/home/akeles/testData/output/uploading-files-main/upload-dir"
directories = glob.glob( inputDirectory + "/*/")

for currDirectory in directories:
    files = [f for f in os.listdir(currDirectory) if os.path.isfile(os.path.join(currDirectory, f))]

    isTxt = all( f.endswith(".txt") for f in files )
    isVisual = all( f.endswith(".PNG") or f.endswith(".png") for f in files )
    isAudioVisual = all( ( f.endswith(".wav") or f.endswith(".png") or f.endswith(".PNG")  ) for f in files )
    
    if isTxt:
        obtainTextInfo(currDirectory, files)
    elif isVisual:            
        thumbnail(currDirectory, files)
        puzzleMetaData = PuzzleMetadata( "Visual", 0 )
        for f in files:
            assetData = imageSearcher( currDirectory + f )
            
            puzzleMetaData.add( assetData )
            
            puzzleMetaData.size = puzzleMetaData.size + assetData.size                        
    
        jsonFile = open( currDirectory + "metadata.json", "w")
        jsonFile.write(puzzleMetaData.toJSON())
        jsonFile.close()  
        
    elif isAudioVisual:
        thumbnail(currDirectory, files)
        puzzleMetaData = PuzzleMetadata( "Audio-Visual", 0 )
        for f in files:
            if f.endswith(".wav") == True:
                assetData = audioSearcher( currDirectory + f )
            else:
                assetData = imageSearcher( currDirectory + f )
            
            puzzleMetaData.add( assetData )
            
            puzzleMetaData.size = puzzleMetaData.size + assetData.size                        
    
        jsonFile = open( currDirectory + "metadata.json", "w")
        jsonFile.write(puzzleMetaData.toJSON())
        jsonFile.close()                                      
            
    else:
        print("Invalid file type")
