
import xml.etree.ElementTree as ET
import re
from html.parser import HTMLParser
from collections import defaultdict
from functools import reduce
import json
import sys
from typing import List
import os
from urllib.parse import unquote
import base64
import zlib


def decompress_diagram(diagram_file: str) -> str:
    """
    Decompresses given xml/drawio file.
    Stolen from Maria
    https://crashlaker.github.io/programming/2020/05/17/draw.io_decompress_xml_python.html
    :param diagram_file: file opened as a string
    :return: string with decompressed file
    """
    diagram_part = re.search("<diagram.*>[\s\S]*?</diagram>", diagram_file)
    part_to_decode = re.sub("</diagram>", "", diagram_part[0])
    part_to_decode = re.sub("<diagram.*>", "", part_to_decode)
    decompress = zlib.decompressobj(-15)
    decompressed_data = decompress.decompress(base64.b64decode(part_to_decode))
    decompressed_data += decompress.flush()
    decoded_diagram = unquote(decompressed_data.decode())
    return decoded_diagram


# https://stackoverflow.com/questions/44542853/how-to-collect-the-data-of-the-htmlparser-in-python-3
class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.d = []
        super().__init__()


    def handle_data(self, data):
        #some hispanic white space https://stackoverflow.com/questions/10993612/how-to-remove-xa0-from-string-in-python
        data = data.replace('&amp;', '&')
        data = data.replace(u'\xa0', u' ')

        self.d.append(data)
        # self.d.append(data.replace(u'\xa0', u' '))
        return (data)

    def return_data(self):
        result = self.d

        self.d =[]

        return result

def loadFromJson(filename):

    file = open(filename)
    data = json.load(file)
    return data

class Vertex:
    def __init__(self, id, content, prodType, color, xPosition, yPosition,vWidth,vHeight):
        self.id = id
        self.content = content
        self.prodType = prodType
        self.color = color
        self.x = xPosition
        self.y = yPosition
        self.width = vWidth
        self.height = vHeight


    def show(self):
        print("Vertex:","\n\tid:", self.id,"\tid:", self.id,"\n\tcontent:", self.content,"\n\ttype:", self.prodType, "\n\tcolor",self.color,"\n\txPos:",self.x,"\n\tyPos:",self.y,"\n\twidth:",self.width,"\n\theight:",self.height)

class Edge:
    def __init__(self, fromId, toId, edgeId):
        self.source = fromId
        self.target = toId
        self.edgeId = edgeId

    def show(self):
        print("Edge from ",self.source," to ",self.target)

class MainStoryProps:
    def __init__(self, mainStoryX, mainStoryY, mainStoryWidth,mainStoryHeight,mainStoryEndX,mainStoryEndY):
        self.x = mainStoryX
        self.y = mainStoryY
        self.width = mainStoryWidth
        self.height = mainStoryHeight
        self.endX = mainStoryEndX
        self.endY = mainStoryEndY





def isVertexColorCorrect(vertex:Vertex, vertexTypesList, vertexColorDict):
    """
    checks if Vertex class instance color attribute is adequate to its type
    :param vertex: Vertex class instance
    :param vertexTypesList: list of strings, naming current vertex types
    :param vertexColorDict: dictionary of possible colors, for each type of vertex
    :return: Boolean, True if color is correct, otherwise False
    """

    for type in vertexTypesList:
        if(vertex.prodType == type):
            return vertex.color.lower() in vertexColorDict[type]

    return False


def mayBeGeneric(production):

    """
    checks if production (content from vertex) suffices regular expressions for generic type

    :param production: string with production, ex. eng name / pl name; (Main_hero, Elixir)

    :return: Boolean
    """
    slashIndex = production.find("/")
    if(slashIndex == -1):
        return False

    beforeSlashRegex ="\s?([A-z\-’`',]+\s)+\s?"
    if(not bool(re.search(beforeSlashRegex,production[0:slashIndex]))):
        return False


    semicolonIndex  = production.find(";")

    if(semicolonIndex == -1):
        return False

    slashToSemicolon = production[slashIndex:semicolonIndex+1]
    slashToSemicolonRegex = "/\s([A-ząćĆęłŁńóÓśŚżŻźŹ\-’`',]+\s?)+\;"

    if(not bool(re.search(slashToSemicolonRegex,slashToSemicolon))):
        return False

    bracketsPart = production[semicolonIndex+1:]
    bracketsRegex ="\s?\((\s?([A-z_/’`'])+\s?,)*\s?([A-z_/’`'])+\s?\)"

    if(not bool(re.search(bracketsRegex,bracketsPart))):
        return False

    return True



def separateArgsFromBrackets(argsInBrackets):
    """
    helper method to obtain arguments list from string starting with brackets
    :param argsInBrackets: ex. (Main_hero,Wizzard)
    :return: list of string args from brackets
    """
    argsList = []

    argsInBrackets = argsInBrackets.strip()
    argsInBrackets = argsInBrackets.replace("(","")

    while "," in argsInBrackets:
        argsInBrackets = argsInBrackets.strip()
        commaAt = argsInBrackets.find(",")
        argsList.append(
            argsInBrackets[0:commaAt].strip()
        )
        argsInBrackets = argsInBrackets[commaAt+1:]

    argsInBrackets = argsInBrackets.replace(")","").strip()

    argsList.append(argsInBrackets)
    return argsList



def checkIfDetailedVertexesAreAllowed(vertexList, allowedDetailedProductionList, testResultDict):
    """
    loop for use of isDetailedProductionAllowed()
    :param vertexList: List containing Vertex entities
    :param allowedDetailedProductionList: allowed productions list, read from json
    :param testResultDict: reference for test dict
    """

    detailedProductionType = "detailed"

    for x in vertexList:
        if(x.prodType == detailedProductionType):
            isDetailedProductionAllowed(x,allowedDetailedProductionList, testResultDict)

def fillTestDict(testResultDict, identifier, elementTitle, infoMessage, messageCategory):
    '''
    :param testResultDict: defaultdict to fill
    :param identifier: id of element to use as a key
    :param elementTitle: title of element, like production
    :param infoMessage: message with what is wrong
    :param messageCategory: type, for now it should be ERROR or WARNING
    '''

    if identifier not in testResultDict:
        testResultDict[identifier] = defaultdict()

    idDict = testResultDict[identifier]


    if "Title" not in idDict:
        idDict["Title"] = elementTitle

    if "Problems" not in idDict:
        idDict["Problems"] = defaultdict()

    problemDict = idDict["Problems"]

    if messageCategory not in problemDict:
        problemDict[messageCategory] = []

    problem = defaultdict()

    problem["Info"] = infoMessage
    problem["Category"] = messageCategory

    problemDict[messageCategory].append(problem) # ew zamiana na stringa


    # testResultDict[vertex.id][production].append(
    #     "ERROR\n\t" + production + "\n\tDetailed production was not found on allowed detailed productions list, check for spelling mistakes")

    # testResultDict.append("ERROR\n\t" +production + "\n\tDetailed production was not found on allowed detailed productions list, check for spelling mistakes" )


def printTestDict(testResultDict:defaultdict):
    for identifier in testResultDict.keys():
        print("Element with Id:", identifier)

        idDict = testResultDict[identifier]

        print("Title: ", idDict["Title"])
        print("Problems:")

        problemsDict = idDict["Problems"]
        # print(problemsDict.keys())
        for key in problemsDict:
            problem = problemsDict[key]
            for p in problem:
                print(key,"\n\t",p["Info"])

        print("\n")


def areThereErrorsInTestDict(testResultDict:defaultdict):
    hasError = False

    for identifier in testResultDict.keys():
        idDict = testResultDict[identifier]
        problemsDict = idDict["Problems"]
        if "ERROR" in problemsDict.keys():
            hasError = True
    return hasError

def isDetailedProductionAllowed(vertex, detailedProductionList, testResultDict):
    """
    checks if production is on allowed json list, by comparing name
    :param vertex: instance of Vertex
    :param allowedDetailedProductionList: allowed productions list, read from json
    :param testResultDict: reference for test dict
    """
    isOnList = False
    # print("val prod",production)
    for p in detailedProductionList:
        # print(production,"\n",p["Title"],"\n", p["Title"]==production,"\n")
        if p["Title"].strip() == vertex.content.strip():
            isOnList = True
    # print("\n")
    if not isOnList:

        message = "Detailed production was not found on allowed detailed productions list, check for spelling mistakes"
        fillTestDict(testResultDict,vertex.id,vertex.content,message,"ERROR")

def checkIfDetailedOrAutomaticVertexesAreAllowed(vertexList, allowedDetailedProductionList, allowedAutomaticProductionList, testResultDict):
    """
    loop for use of isDetailedProductionAllowed()
    :param vertexList: List containing Vertex entities
    :param allowedDetailedProductionList: allowed productions list, read from json
    :param testResultDict: reference for test dict
    """

    detailedProductionType = "detailed"

    for x in vertexList:
        if(x.prodType == detailedProductionType):
            isDetailedOrAutomaticProductionAllowed(x, allowedDetailedProductionList, allowedAutomaticProductionList, testResultDict)

def isDetailedOrAutomaticProductionAllowed(vertex, detailedProductionList, automaticProductionList, testResultDict):
    """
    checks if production is on allowed json lists, by comparing name
    use of generic productions is due to similar form of detailed and automatic productions

    :param vertex: string name of production, format. Eng name / Pl name
    :param automaticProductionList: allowed generic productions list, read from json
    :param detailedProductionList: allowed productions list, read from json
    :param testResultDict: reference for test dict
    """
    isOnList = False
    # print("val prod",production)
    for p in detailedProductionList:
        # print(production,"\n",p["Title"],"\n", p["Title"]==production,"\n")
        if p["Title"].strip() == vertex.content.strip():
            isOnList = True

    if not isOnList:
        for p in automaticProductionList:
            # print(production,"\n",p["Title"],"\n", p["Title"]==production,"\n")
            if p["Title"].strip() == vertex.content.strip():
                isOnList = True

                message = "Automatic production detected. Make sure if there should be no args. You can ignore color warning for this one"
                fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")

    # print("\n")
    if not isOnList:

        message = "Production was not found on allowed detailed and automatic productions lists, check for spelling mistakes"
        fillTestDict(testResultDict, vertex.id, vertex.content, message, "ERROR")

        # testResultDict.append("ERROR\n\t" +production + "\n\tDetailed production was not found on allowed detailed productions list, check for spelling mistakes" )

def isGenericProductionAllowed(vertex, genericProductionList, charactersList, itemsList, locationsList, testResultDict):
    """
    checks if production is on allowed json list, by comparing name,
    checks if arguments in brackets are on one of allowed lists,
    counts and checks number of arguments

    :param vertex: string name of production, format. Eng name / Pl name; (Arg, Arg)
    :param genericProductionList: allowed generic productions, read from json
    :param charactersList: allowed characters list
    :param itemsList: allowed items list
    :param locationsList: allowed locations list
    :param testResultDict: reference for test dict

    :return Boolean
    """
    begIndex = 0
    if vertex.content[0] == " ":
        begIndex = 1

    semicolonIndex = vertex.content.find(";")

    if vertex.content[semicolonIndex] == " ":
        semicolonIndex -=1

    titlePart = vertex.content[begIndex:semicolonIndex]
    isOnList = False

    for p in genericProductionList:
        if p["Title"] == titlePart:

            isOnList = True

    if not isOnList:

        if "`" in vertex.content or "'" in vertex.content:
            message = "Generic production was not found on allowed generic productions list, check for accidental ' apostrophes, (maybe ’)"
            fillTestDict(testResultDict, vertex.id, vertex.content, message, "ERROR")

        else:
            message = "Generic production was not found on allowed generic productions list, check for spelling mistakes"
            fillTestDict(testResultDict, vertex.id, vertex.content, message, "ERROR")

        return False


    bracketPart = vertex.content[semicolonIndex + 1:]
    bracketPart = bracketPart.strip()

    argsInBrackets = separateArgsFromBrackets(bracketPart)

    # count args
    commaCount = bracketPart.count(',')
    if (commaCount != 0):
        argsCount = commaCount + 1
    else:
        argsCount = 1

    charactersCount = 0
    itemsCount = 0
    connectionsCount =0
    narrationCount = 0

    # print("!!")
    for p in genericProductionList:
        if p["Title"] in titlePart:
            loc = p["LSide"]
            characsloc = loc["Locations"]

            for i in characsloc[0]["Characters"]:
                # for c in i:
                # print(list(i))

                # if ["Id"] in list(i):
                # print(i)
                if "Id" in i:
                    charactersCount += 1
                    # print(i)
                # charactersCount += 1

                if("Items" in  i ):
                    itemsCount += len(i["Items"])
                    # for ids in i["Items"]:
                    #     # if ["Id"] in ids:
                    #     print(ids)
                    # print(i["Items"])

                if ("Narration" in i):
                    narrationCount +=1

            # if "Narration" in characsloc[0]:
            #     for i in characsloc[0]["Narration"]:
            #         charactersCount += 1
            #         if("Items" in  i ):
            #             itemsCount += len(i["Items"])


            if "Items" in characsloc[0]:
                for i in characsloc[0]["Items"]:
                    # print(i)
                    if "Id" in i:
                        charactersCount += 1

                    if("Items" in  i ):
                        itemsCount += len(i["Items"])
                        # for it in i["Items"]:
                        #     print(i)

                    if ("Narration" in i):
                        narrationCount +=1



            if "Location change" in vertex.content:
                if(argsCount == 2):
                    return True
            if "Picking item" in vertex.content or "Dropping item" in vertex.content:
                if(argsCount == 1):
                    return True

            if charactersCount + itemsCount + connectionsCount + narrationCount != argsCount:
                message = "Check amount of args in production"
                fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")

                if argsCount == 1:
                    message = "Check amount of args in production"
                    fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")


                elif "Location change" in vertex.content:
                    message = "Check amount of args in production"
                    fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")

                else:
                    message = "Check amount of args in production, expected " + str(charactersCount + itemsCount + connectionsCount + narrationCount) + ", but got " + str(argsCount)

                    fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")


    for arg in argsInBrackets:
        if (arg not in charactersList) and (arg not in itemsList) and (arg not in locationsList) :
            if "/" in arg:
                slashArgs = arg.split('/')
                areSlashArgsCorrect = True
                # print(slashArgs)
                for sa in slashArgs:
                    if (sa not in charactersList) and (sa not in itemsList) and (sa not in locationsList):
                        # zamiast errora - slashe
                        message = "In arg: " + arg + ", this arg " + sa + " was not found on Characters/Items/Locations list, check for spelling mistakes"
                        fillTestDict(testResultDict, vertex.id, vertex.content, message, "ERROR")

                #
            else:

                if narrationCount > 0:
                    message = arg + " is not on allowed Characters/Items/Locations list, Narration element was detected, Ignore if its narration"
                    fillTestDict(testResultDict, vertex.id, vertex.content, message, "WARNING")

                else:
                    message = arg + " is not on allowed Characters/Items/Locations list, check for spelling mistakes"
                    fillTestDict(testResultDict, vertex.id, vertex.content, message, "ERROR")



    return True


def parseColor(style):
    """
    find color bycolor string from style cropped from drawing xml
    :param style: attrib["style"] from drawing
    :return: string color
    """
    fillColorTag ="fillColor"
    hexColorLen = 7 # with #xxxxxx
    if style.find(fillColorTag) == -1:
        return "none"


    begColorIndex = style.index(fillColorTag) + len(fillColorTag) +1
    endColorIndex = begColorIndex + hexColorLen


    return style[begColorIndex:endColorIndex]


def getNeighboursIds(vertexId, edgeDict):
    """
    finds list of neighbouring vertexes ids
    :param production: string name of production, format. Eng name / Pl name; (Arg, Arg)
    :param edgeDict: dictionary of key: vertexId, value: list of Edge entities, which source is vertex of id key

    :return list of neighbouring vertexes ids
    """
    # print("checkup ", vertexId)
    neigboursList = edgeDict.get(vertexId)
    neigboursIdList = []
    # print(neigboursList)

    if bool(neigboursList):
        for e in neigboursList:
            neigboursIdList.append(e.target)
    else:
        neigboursIdList = []

    return neigboursIdList


def dfsToEnding(vertexDict, edgeDict, visitedList, foundEnding, currentVertex):
    """
    Checks if there is any ending using pseudo DFS search, use only on non ending vertexes

    :param vertexDictdictionary of key: vertexId value: Vertex entity
    :param edgeDict: dictionary of key: vertexId value: list of Edge entities, which source is vertex of id key
    :param visitedList: list of already visited vertex ids, should be empty at first
    :param foundEnding: List containing Boolean value if ending was found, list is there to keep reference value in recursion, use of this param should be done with [False], so search is done
    :param currentVertex - string id of current vertex, use one where you want to start

    :return Boolean
    """
    visitedList.append(currentVertex)

    neighboursIds = getNeighboursIds(currentVertex,edgeDict)

    endingProductionType = "ending"


    if( vertexDict.get(currentVertex).prodType == endingProductionType):
        foundEnding[0] = True

    if foundEnding[0]:
        return True # found an ending from vertex

    for vId in neighboursIds:
        if foundEnding[0]:
            return True

        if vId not in visitedList:
            return dfsToEnding(vertexDict,edgeDict,visitedList,foundEnding,vId)

    if foundEnding[0]:
        return True # found an ending from vertex


    return False


def readEdgesAndVertexFromOpenedDrawing(drawingFile, vertexListToFill, edgeListToFill, edgeDictToFill, mainStoryPropsToFill, testResultDict, notAllowedShapesList):
    if "root" not in drawingFile:
        drawingFile = decompress_diagram(drawingFile)

    tree = ET.ElementTree(ET.fromstring(drawingFile))


    root = tree.getroot()
    parser = MyHTMLParser()
    mainStoryWidth= 0


    endingProductionType = "ending"

    for elem in root.iter('mxCell'):
        if "edge" in elem.attrib:

            if(("source" not in elem.attrib ) or ("target" not in elem.attrib)):
                if elem.attrib["id"] not in testResultDict:
                    testResultDict[elem.attrib["id"]] = defaultdict()  # było [] POPRAWKA IGG
                edge_x = 0
                edge_y = 0
                for geometry in elem.iter('mxGeometry'):
                    for point in geometry.iter('mxPoint'):
                        edge_x = point.attrib["x"]
                        edge_y = point.attrib["y"]



                message = "Edge with id " + str(elem.attrib["id"]) +"is not connected to source or target properly, coordinates: (" + str(edge_x) + "," + str(edge_y) +")"
                fillTestDict(testResultDict, str(elem.attrib["id"]), "EDGE", message, "ERROR")
                # foundAtLeastBadEdge = True
                continue

            if("source" in elem.attrib ) and ("target" in elem.attrib):
                edgeListToFill.append(Edge(
                    elem.attrib["source"],
                    elem.attrib["target"],
                    elem.attrib["id"]
                ))




            if not bool(edgeDictToFill.get(elem.attrib["source"])):
                edgeDictToFill[elem.attrib["source"]] = []
                edgeDictToFill[elem.attrib["source"]].append(
                    Edge(
                        elem.attrib["source"],
                        elem.attrib["target"],
                        elem.attrib["id"]
                    ))
                continue

            edgeDictToFill[elem.attrib["source"]].append(
                Edge(
                    elem.attrib["source"],
                    elem.attrib["target"],
                    elem.attrib["id"]
                ))
            continue




        if "vertex" in elem.attrib:

            allowedShape = True
            for s in notAllowedShapesList:
                if s in elem.attrib["style"]:

                    message = str(s)+" Vertex shape is not allowed, skipping this vertex in checkups"
                    fillTestDict(testResultDict, str(elem.attrib["id"]),"SHAPE" , message, "ERROR")

                    foundAtLeastBadOneVertex = True
                    continue





            if "ellipse" in elem.attrib["style"]:

                # move getting positions to method later, here and in normal vertex
                for geometry in elem.iter('mxGeometry'):
                    if 'x' in geometry.attrib:
                        xPos = geometry.attrib['x']
                        hasX = True
                    if 'y' in geometry.attrib:
                        yPos = geometry.attrib['y']
                        hasY = True
                    if 'width' in geometry.attrib:
                        width = geometry.attrib['width']
                        hasWidth = True
                    if 'height' in geometry.attrib:
                        height = geometry.attrib['height']
                        hasHeight = True
                if not (hasX and hasY and hasWidth and hasHeight):
                    hasX = False
                    hasY = False
                    hasWidth = False
                    hasHeight = False
                    foundAtLeastBadOneVertex = True

                    message = str(elem.attrib[
                            "id"]) + ' is not proper FINAL vertex, has no x or y position or no width, skipping this vertex in later checkups'

                    fillTestDict(testResultDict, str(elem.attrib["id"]), "FINAL", message, "ERROR")

                if "value" in elem.attrib and not elem.attrib["id"] == "":
                    if( bool(re.search("\s?[1-9][0-9]?\s?",elem.attrib["value"]))):
                        vertexListToFill.append(
                            Vertex(elem.attrib["id"],
                                   elem.attrib["value"].replace("<br>","\n"),
                                   endingProductionType,
                                   parseColor(elem.attrib["style"]),
                                   float(xPos),
                                   float(yPos),
                                   float(width),
                                   float(height)
                                   ))
                else:

                    message = str(elem.attrib[
                                      "id"]) + ' Unexpected value in ending production (not a mission number)'

                    fillTestDict(testResultDict, str(elem.attrib["id"]), "FINAL", message, "ERROR")




                vertexListToFill.append(
                    Vertex(elem.attrib["id"],
                           "",
                           endingProductionType,
                           parseColor(elem.attrib["style"]),
                           float(xPos),
                           float(yPos),
                           float(width),
                           float(height)
                           )
                )

                continue # to not vertex it again

            if "#fff2cc" in elem.attrib["style"].lower() and mainStoryWidth==0 and ("ellipse" not in elem.attrib["style"]):
                for geometry in elem.iter('mxGeometry'):
                    mainStoryPropsToFill.x = float(geometry.attrib['x'])
                    mainStoryPropsToFill.y = float(geometry.attrib['y'])
                    mainStoryPropsToFill.width = float(geometry.attrib['width'])
                    mainStoryPropsToFill.height = float(geometry.attrib['height'])
                    mainStoryPropsToFill.endX = float(mainStoryPropsToFill.x + mainStoryPropsToFill.width/2 )
                    mainStoryPropsToFill.endY = float(mainStoryPropsToFill.y + mainStoryPropsToFill.height)
                continue



            hasX = False
            hasY= False


            parser.feed(elem.attrib["value"].replace("<br>","\n"))
            for geometry in elem.iter('mxGeometry'):

                if 'x' in geometry.attrib:
                    xPos = geometry.attrib['x']
                    hasX = True
                if 'y' in geometry.attrib:
                    yPos = geometry.attrib['y']
                    hasY = True
                if 'width' in geometry.attrib:
                    width = geometry.attrib['width']
                    hasWidth = True
                if 'height' in geometry.attrib:
                    height = geometry.attrib['height']
                    hasHeight= True
            if not (hasX and hasY and hasWidth and hasHeight):
                hasX=False
                hasY=False
                hasWidth = False
                hasHeight= False
                foundAtLeastBadOneVertex = True

                message = str(elem.attrib["value"]) + ' is not proper vertex, has no x or y position or no width, skipping this vertex in later checkups'

                fillTestDict(testResultDict, str(elem.attrib["id"]), str(elem.attrib["value"]), message, "ERROR")

                continue


            vertexListToFill.append(
                Vertex(elem.attrib["id"],
                       reduce(lambda a,b: a+b,parser.return_data()),
                       "type",
                       parseColor(elem.attrib["style"]),
                       float(xPos),
                       float(yPos),
                       float(width),
                       float(height)
                       )
            )

            continue

# to be removed
# def readEdgesAndVertexFromXml(drawingFileLocation, vertexListToFill, edgeListToFill, edgeDictToFill, mainStoryPropsToFill, testResultDict, notAllowedShapesList):
#     """
#     Fills vertex list, edge list, edge dictionary, main story positional properties and test result list
#     Should be used first, to load from XML correctly
#
#     :param drawingFileLocation: path to drawing XML file
#     :param vertexListToFill: empty list reference, to be filled with Vertex entities
#     :param edgeListToFill: empty list reference, to be filled with edge entities
#     :param edgeDictToFill: empty default dictionary reference, to be filled with edge entities
#     :param mainStoryPropsToFill: Entity of MainStoryProps
#     :param testResultDict: dict to store test results
#     :param notAllowedShapesList: list to be passed for checks, take it from constants at top of file
#     """
#
#     # stolen from Maria
#     drawingFile =open(drawingFileLocation, encoding="utf-8").read()
#     if "root" not in drawingFile:
#         drawingFile = decompress_diagram(drawingFile)
#         tree = ET.ElementTree(ET.fromstring(drawingFile))
#
#     else:
#         tree = ET.parse(drawingFileLocation)
#
#     root = tree.getroot()
#     parser = MyHTMLParser()
#     mainStoryWidth= 0
#
#
#     endingProductionType = "ending"
#
#     for elem in root.iter('mxCell'):
#         if "edge" in elem.attrib:
#
#             if(("source" not in elem.attrib ) or ("target" not in elem.attrib)):
#                 if elem.attrib["id"] not in testResultDict:
#                     testResultDict[elem.attrib["id"]] =[]
#                 edge_x = 0
#                 edge_y = 0
#                 for geometry in elem.iter('mxGeometry'):
#                     for point in geometry.iter('mxPoint'):
#                         edge_x = point.attrib["x"]
#                         edge_y = point.attrib["y"]
#
#
#                 testResultDict[elem.attrib["id"]].append(
#                     'ERROR\n\tedge with id ' + str(elem.attrib["id"]) +"\n\tis not connected to source or target properly, coordinates: (" + str(edge_x) + "," + str(edge_y) +")"
#                 )
#                 # foundAtLeastBadEdge = True
#                 continue
#
#             if("source" in elem.attrib ) and ("target" in elem.attrib):
#                 edgeListToFill.append(Edge(
#                     elem.attrib["source"],
#                     elem.attrib["target"],
#                     elem.attrib["id"]
#                 ))
#
#
#
#
#             if not bool(edgeDictToFill.get(elem.attrib["source"])):
#                 edgeDictToFill[elem.attrib["source"]] = []
#                 edgeDictToFill[elem.attrib["source"]].append(
#                     Edge(
#                         elem.attrib["source"],
#                         elem.attrib["target"],
#                         elem.attrib["id"]
#                     ))
#                 continue
#
#             edgeDictToFill[elem.attrib["source"]].append(
#                 Edge(
#                     elem.attrib["source"],
#                     elem.attrib["target"],
#                     elem.attrib["id"]
#                 ))
#             continue
#
#
#
#
#         if "vertex" in elem.attrib:
#
#             allowedShape = True
#             for s in notAllowedShapesList:
#                 if s in elem.attrib["style"]:
#                     if str(s) not in testResultDict:
#                         testResultDict[str(s)] =[]
#                     testResultDict[str(s)].append("ERROR\n\t"+str(s)+" vertex shape is not allowed, skipping this vertex in checkups")
#                     foundAtLeastBadOneVertex = True
#                     continue
#
#
#
#
#
#             if "ellipse" in elem.attrib["style"]:
#
#                 # move getting positions to method later, here and in normal vertex
#                 for geometry in elem.iter('mxGeometry'):
#                     if 'x' in geometry.attrib:
#                         xPos = geometry.attrib['x']
#                         hasX = True
#                     if 'y' in geometry.attrib:
#                         yPos = geometry.attrib['y']
#                         hasY = True
#                     if 'width' in geometry.attrib:
#                         width = geometry.attrib['width']
#                         hasWidth = True
#                     if 'height' in geometry.attrib:
#                         height = geometry.attrib['height']
#                         hasHeight = True
#                 if not (hasX and hasY and hasWidth and hasHeight):
#                     hasX = False
#                     hasY = False
#                     hasWidth = False
#                     hasHeight = False
#                     foundAtLeastBadOneVertex = True
#                     if str(elem.attrib["value"]) not in testResultDict:
#                         testResultDict[str(elem.attrib["value"])] = []
#
#                     testResultDict[str(elem.attrib["value"])].append('ERROR\n\t' + str(elem.attrib["id"]) + '\n\tis not proper FINAL vertex, has no x or y position or no width, skipping this vertex in later checkups')
#
#                 if "value" in elem.attrib and not elem.attrib["id"] == "":
#                     if( bool(re.search("\s?[1-9][0-9]?\s?",elem.attrib["value"]))):
#                         vertexListToFill.append(
#                             Vertex(elem.attrib["id"],
#                                    elem.attrib["value"].replace("<br>","\n"),
#                                    endingProductionType,
#                                    parseColor(elem.attrib["style"]),
#                                    float(xPos),
#                                    float(yPos),
#                                    float(width),
#                                    float(height)
#                                    ))
#                 else:
#                     if str( elem.attrib["id"]) not in testResultDict:
#                         testResultDict[ str( elem.attrib["id"])] =[]
#                     testResultDict[ str( elem.attrib["id"])].append('ERROR\n\t'+'check id: '+ str( elem.attrib["id"])+'\n\tUnexpected value in ending production (not a mission number)')
#
#
#
#                 vertexListToFill.append(
#                     Vertex(elem.attrib["id"],
#                            "",
#                            endingProductionType,
#                            parseColor(elem.attrib["style"]),
#                            float(xPos),
#                            float(yPos),
#                            float(width),
#                            float(height)
#                            )
#                 )
#
#                 continue # to not vertex it again
#
#             if "#fff2cc" in elem.attrib["style"].lower() and mainStoryWidth==0 and ("ellipse" not in elem.attrib["style"]):
#                 for geometry in elem.iter('mxGeometry'):
#                     mainStoryPropsToFill.x = float(geometry.attrib['x'])
#                     mainStoryPropsToFill.y = float(geometry.attrib['y'])
#                     mainStoryPropsToFill.width = float(geometry.attrib['width'])
#                     mainStoryPropsToFill.height = float(geometry.attrib['height'])
#                     mainStoryPropsToFill.endX = float(mainStoryPropsToFill.x + mainStoryPropsToFill.width/2 )
#                     mainStoryPropsToFill.endY = float(mainStoryPropsToFill.y + mainStoryPropsToFill.height)
#                 continue
#
#
#
#             hasX = False
#             hasY= False
#
#
#             parser.feed(elem.attrib["value"].replace("<br>","\n"))
#             for geometry in elem.iter('mxGeometry'):
#
#                 if 'x' in geometry.attrib:
#                     xPos = geometry.attrib['x']
#                     hasX = True
#                 if 'y' in geometry.attrib:
#                     yPos = geometry.attrib['y']
#                     hasY = True
#                 if 'width' in geometry.attrib:
#                     width = geometry.attrib['width']
#                     hasWidth = True
#                 if 'height' in geometry.attrib:
#                     height = geometry.attrib['height']
#                     hasHeight= True
#             if not (hasX and hasY and hasWidth and hasHeight):
#                 hasX=False
#                 hasY=False
#                 hasWidth = False
#                 hasHeight= False
#                 foundAtLeastBadOneVertex = True
#                 if str(elem.attrib["value"]) not in testResultDict:
#                     testResultDict[ str(elem.attrib["value"])] =[]
#
#                 testResultDict[ str(elem.attrib["value"])].append('ERROR\n\t'+str(elem.attrib["value"]) + '\n\tis not proper vertex, has no x or y position or no width, skipping this vertex in later checkups')
#                 continue
#
#
#             vertexListToFill.append(
#                 Vertex(elem.attrib["id"],
#                        reduce(lambda a,b: a+b,parser.return_data()),
#                        "type",
#                        parseColor(elem.attrib["style"]),
#                        float(xPos),
#                        float(yPos),
#                        float(width),
#                        float(height)
#                        )
#             )
#
#             continue


def checkVertexAlignmentInMainStory(vertexList:List[Vertex],mainStoryProps:MainStoryProps,testResultDict):
    """
    Checks if Vertexes inside main story area are alligned by middle axis
    Before this method call readEdgesAndVertexFromXml, so MainStoryProps is filled

    :param vertexList: list of vertexes to check, ones inside area are verified
    :param mainStoryProps: entity of MainStoryProps, which is used for verification
    :param testResultDict: dictionary to be filled with potential errors
    """
    # fix this method
    mainStoryFirstXValue = []
    for x in vertexList:
        if ( x.x > mainStoryProps.x) and ( x.y > mainStoryProps.y) and ( x.x < mainStoryProps.endX) and (x.y < mainStoryProps.endY):
            if len(mainStoryFirstXValue) == 0:
                mainStoryFirstXValue.append(x.x)

            if len(mainStoryFirstXValue) >0:
                if x.x != mainStoryFirstXValue[0]:

                    message = "Check if vertexes are alligned in main story"

                    fillTestDict(testResultDict, str(x.id), str(x.content), message, "WARNING")

def checkIfVertexesAreIntersecting(vertexList:List[Vertex],testResultDict):
    """
    Checks if vertexes on list are intersecting, if two are, test dict at key "INTERSECTING" is appended

    :param vertexList: list of Vertex entities to verify
    :param testResultDict: dict to be appended with errors

    """
    endingProductionType = "ending"

    for v in vertexList:
        for v2 in vertexList:

            if (v != v2):
                if (v2.x >= v.x and v2.x <= v.x + v.width) and ((v2.y + v2.height > v.y and v2.y + v2.height < v.y + v.height) or (v2.y > v.y  and v2.y < v.y + v.height)):

                    # if str("INTERSECTING") not in testResultDict:
                    #     testResultDict["INTERSECTING"] = []

                    if(v.prodType == endingProductionType):
                        vDesc = "Ending production at (" + str(v.x) + "," + str(v.y) + ")"
                    else:
                        vDesc = v.content + " at (" + str(v.x) + "," + str(v.y) + ")"

                    if(v2.prodType == endingProductionType):
                        v2Desc = "Ending production at (" + str(v2.x) + "," + str(v2.y) + ")"
                    else:
                        v2Desc = v2.content + " at (" + str(v2.x) + "," + str(v2.y) + ")"

                    message = vDesc+ ' is intersecting with ' +v2Desc

                    fillTestDict(testResultDict, v.id, v.content, message, "ERROR")
                    fillTestDict(testResultDict, v2.id, v2.content, message, "ERROR")

def checkProductionTypesByRegex(vertexList:List[Vertex],testResultDict):
    """
    Checks production type with regexes,
    if type is known, then type is assigned to Vertex entity
    otherwise test result list is appended with proper error

    TYPE ASSIGNED HERE IS USED IN OTHER CHECKS.

    TO BE USED BEFORE FOLLOWING: checkVertexListColors(), checkIfDetailedVertexesAreAllowed(vertexList,allowedDetailedProductionList,testResultDict), checkIfGenericVertexesAreAllowed()

    :param vertexList: list of Vertex entities to verify
    :param testResultDict: dict to be appended with errors

    """
    missionProductionType= "mission"
    genericProductionType = "generic"
    detailedProductionType = "detailed"
    endingProductionType = "ending"
    missionProductionRegex = "^\(\s?(\w\s*)+[?|!]?\s?,\s?Q[0-9]+\s?(\)\s?)$"
    detailedProductionRegex = "s?([0-9A-z_-’`',]+\s)+\s?/\s?([0-9A-ząćĆęłŁńóÓśŚżŻźŹ\-_’`',]+\s?)+"

    for x in vertexList:


        if(mayBeGeneric(x.content)):
            x.prodType = genericProductionType
            continue

        if(bool(re.search(missionProductionRegex,x.content))):
            x.prodType = missionProductionType
            continue

        if(bool(re.match(detailedProductionRegex,x.content)) and "(" not in x.content and ";" not in x.content):

            x.prodType = detailedProductionType
            continue

        if( x.prodType != endingProductionType and "!" in x.content):

            message = "Production name does not seem to fit any proper format of production, check '!'"
            fillTestDict(testResultDict, x.id, str(x.content), message, "ERROR")


        elif( x.prodType != endingProductionType):

            message = "Production name does not seem to fit any proper format of production"
            fillTestDict(testResultDict, x.id, str(x.content), message, "ERROR")


def copyVertexListToDict(vertexList:List[Vertex],vertexDict):
    """
    Fills dict with vertexes on list, by following schema:
    key: vertex id, value: Vertex entity

    :param vertexList: list of Vertex entities to verify
    :param vertexDict: default dict to be filled with key: vertex id, value: Vertex entity

    """
    for v in vertexList:
        vertexDict[v.id] = v

def checkVertexListColors(vertexList, testResultDict,allowedColorDictionary):
    """
    Verifies if color from dictionary fits production type in entity

    :param vertexList: list of Vertex entities to verify
    :param testResultDict: dict to be appended with errors
    :param allowedColorDictionary: dict with key: prod type, value: list of allowed colors

    """

    missionProductionType= "mission"
    detailedProductionType = "detailed"
    endingProductionType = "ending"
    genericProductionType = "generic"

    vertexTypesList = [missionProductionType,detailedProductionType,endingProductionType,genericProductionType]

    for x in vertexList:
        if x.prodType == "type":
            message = "Skipped color check as production type was not recognized"
            fillTestDict(testResultDict, x.id, str(x.content), message, "WARNING")

        elif not isVertexColorCorrect(x,vertexTypesList,allowedColorDictionary) and (x.color.lower() in allowedColorDictionary[genericProductionType] ):

            message = "Found color in production" + x.color + ", make sure its generic production(generic colors are none or #ffffff). If it is, ignore warning"
            fillTestDict(testResultDict, x.id, str(x.content), message, "WARNING")

        elif not isVertexColorCorrect(x,vertexTypesList,allowedColorDictionary):

            message = "Color " + x.color+" in production of type "+x.prodType +" is not on allowed list: " + str(allowedColorDictionary[x.prodType])
            fillTestDict(testResultDict, x.id, str(x.content), message, "ERROR")



def checkIfGenericVertexesAreAllowed(vertexList, allowedGenericProductionList, charactersList, itemsList, locationsList, testResultDict):
    """
    loop for calling isGenericProductionAllowed()

    :param vertexList: list of Vertex entities to verify
    :param allowedGenericProductionList: allowed generic productions, read from json
    :param charactersList: allowed characters list
    :param itemsList: allowed items list
    :param locationsList: allowed locations list
    :param testResultDict: reference for test dict

    """
    genericProductionType = "generic"

    for x in vertexList:
        if(x.prodType == genericProductionType):
            isGenericProductionAllowed(x,allowedGenericProductionList,charactersList, itemsList, locationsList, testResultDict)


def checkOutgoingEdgesCorrectness(vertexDict,edgeDict,testResultDict):
    """
    checks if vertexes have outgoing edges

    :param vertexDict
    :param edgeDict
    :param testResultDict: dict w err
    """
    endingProductionType = "ending"
    for v in vertexDict.values():

        if not bool(edgeDict.get(v.id)):
            if v.prodType != endingProductionType:

                message = "No outgoing edges from non-ending vertex"
                fillTestDict(testResultDict, v.id, str(v.content), message, "ERROR")


        if bool(edgeDict.get(v.id)) and v.prodType == endingProductionType:

            message = "Ending should not have outgoing edges"
            fillTestDict(testResultDict, v.id, "ENDING", message, "ERROR")


def startingChecks(vertexList, vertexDict,edgeList, edgeDict,testResultDict):
    """
    checks if there is starting edge by 2 criteria, first - not having incoming edges, second - having all vertex that are sources to incoming edges below

    :param vertexList
    :param edgeList
    :param vertexDict
    :param edgeDict
    :param testResultDict
    """
    suspectedStartingVertex = []

    suspectedStartingVertex = list(edgeDict.keys())

    # checking vertex with no incoming edge
    for edgeList in edgeDict.values():

        for edge in edgeList:

            for suspect in suspectedStartingVertex:
                if suspect == edge.target:
                    suspectedStartingVertex.remove(suspect)




    # second part, ones with incoming vertexes
    for v in vertexList:
        isStarting = False
        for e in edgeList:
            if e.target == v.id:
                if vertexDict[e.target].y < v.y:
                    isStarting = True
                else:
                    isStarting = False
                    break # breaking loop as one incoming edge is higher


        if isStarting:
            suspectedStartingVertex.append(suspectedStartingVertex)

    # end of starting finding validation


    if (len(suspectedStartingVertex )== 0 ):

        message = "Could not find staring point, make sure that it is higher than any vertex pointing to it or has no incoming edges"
        fillTestDict(testResultDict, "START", "START", message, "ERROR")



    if(len(suspectedStartingVertex) > 1):

        message = "More than one vertex is a starting point (no incoming edges or its higher than all incoming edges), please check if there should be more than one starting points"
        fillTestDict(testResultDict, "START", "START", message, "WARNING")

def getNeighboursIds(vertexId, edgeDict):
    """
    Finds list of neighbouring ids of vertex of given id, based on edge dictionary
    Dictionary can be filled with readEdgesAndVertexFromXml()

    :param vertexId: string id of vertex
    :param edgeDict: dictionary of key: source vertex id string, value: Edge entities, for which this id is source

    :return list of stirng ids of neighbours
    """

    neigboursList = edgeDict.get(vertexId)
    neigboursIdList = []

    if bool(neigboursList):
        for e in neigboursList:
            neigboursIdList.append(e.target)
    else:
        neigboursIdList = []

    return neigboursIdList

# foundEnding = [False] # to keep reference
def dfsToEnding(vertexDict, edgeDict, visitedIdList, foundEnding, currentVertexId):
    """
    Checks if there is any ending using pseudo DFS search, use only on non ending vertexes
    :param vertexDictdictionary of key: vertexId value: Vertex entity
    :param edgeDict: dictionary of key: vertexId value: list of Edge entities, which source is vertex of id key

    :param visitedList: list of already visited vertex ids, should be empty at first
    :param foundEnding: List containing Boolean value if ending was found, list is there to keep reference value in recursion, use of this param should be done with [False], so search is done
    :param currentVertex - string id of current vertex, use one where you want to start

    :return Boolean
    """
    endingProductionType = "ending"


    visitedIdList.append(currentVertexId)

    neighboursIds = getNeighboursIds(currentVertexId,edgeDict)


    if( vertexDict.get(currentVertexId).prodType == endingProductionType):
        foundEnding[0] = True

    if foundEnding[0]:
        return True # found an ending from vertex

    for vId in neighboursIds:
        if foundEnding[0]:
            return True

        if vId not in visitedIdList:
            return dfsToEnding(vertexDict,edgeDict,visitedIdList,foundEnding,vId)

    if foundEnding[0]:
        return True # found an ending from vertex


    return False

def checkIfAnyEndingFoundFromEveryVertex(vertexList,vertexDict,edgeDict, testResultDict, foundAtLeastOneBadVertex):
    """
    Checks if there is any ending using pseudo DFS search, use only on non ending vertexes
    :param vertexDictdictionary of key: vertexId value: Vertex entity
    :param edgeDict: dictionary of key: vertexId value: list of Edge entities, which source is vertex of id key

    :param visitedList: list of already visited vertex ids, should be empty at first
    :param foundEnding: List containing Boolean value if ending was found, list is there to keep reference value in recursion, use of this param should be done with [False], so search is done
    :param currentVertex - string id of current vertex, use one where you want to start

    :return Boolean
    """
    endingProductionType = "ending"



    foundEnding = [False] # to keep reference
    visitedList = []
    foundEnding = [False]
    if not foundAtLeastOneBadVertex:

        for v in vertexList:
            visitedList = []
            foundEnding = [False]

            if v.prodType != endingProductionType:
                foundEnding = [False]
                if not dfsToEnding(vertexDict,edgeDict,visitedList,foundEnding,v.id):

                    message = "Could not reach any ending from vertex, check connections"
                    fillTestDict(testResultDict, v.id, v.content, message, "ERROR")

    else:

        message = "Skipped ending search from each vertex"
        fillTestDict(testResultDict, "SKIPPED DFS", "SKIPPED DFS", message, "WARNING")



def validate_drawing(drawingFile, allowedCharactersList, allowedItemsList, allowedLocationsList,
                     allowedGenericProductionList, allowedDetailedProductionList, allowedAutomaticProductionList):

    """
    validates drawing file (opened, not path) passed in args, based on allowed lists. Example of usage in validator.py

    :param drawingFile: already opened xml file with compressed or uncompressed drawing
    :param allowedCharactersList: characters list, already read from json
    :param allowedItemsList: items list, already read from json
    :param allowedLocationsList: locations list, already read from json
    :param allowedGenericProductionList: generic productions list, already read from json
    :param allowedDetailedProductionList: detailed productions list, already read from json
    :param allowedAutomaticProductionList: automatic productionslist, already read from json

    :return test result dictionary, K: Identifying name (vertex content/edge id) V: list of warnings and errors for key
    """


    # DEFINIOWANIE WARTOŚCI OBIEKTÓW
    missionProductionType = "mission"
    genericProductionType = "generic"
    detailedProductionType = "detailed"
    endingProductionType = "ending"
    allowedColorDictionary = defaultdict()
    allowedColorDictionary[missionProductionType] = "#e1d5e7"
    allowedColorDictionary[genericProductionType] = {"#ffffff", "none"}
    allowedColorDictionary[detailedProductionType] = "#ffe6cc"
    allowedColorDictionary[endingProductionType] = {"#fff2cc", "#000000", "#f5f5f5", "#e1d5e7", "none", "none;"}

    notAllowedShapesList = ["rhombus", "process", "parallelogram", "hexagon", "cloud"]

    mainStoryProps = MainStoryProps(0, 0, 0, 0, 0, 0)

    # INICJALIZOWANIE STRUKTUR
    vertexList = []
    vertexDict = defaultdict()
    edgeList = []
    edgeDict = defaultdict()
    testResultDict = defaultdict()

    # LOADING PART

    # readEdgesAndVertexFromXml(drawingFile,vertexList,edgeList,edgeDict, mainStoryProps,testResultDict,notAllowedShapesList)
    readEdgesAndVertexFromOpenedDrawing(drawingFile, vertexList, edgeList, edgeDict, mainStoryProps, testResultDict,
                                        notAllowedShapesList)

    copyVertexListToDict(vertexList, vertexDict)

    checkProductionTypesByRegex(vertexList, testResultDict)

    # TYPE RELATED CHECK PART
    # depends on checkProductionTypesByRegex(), types are assigned there
    checkVertexListColors(vertexList, testResultDict, allowedColorDictionary)

    # depends on checkProductionTypesByRegex(), types are assigned there
    checkIfDetailedOrAutomaticVertexesAreAllowed(vertexList, allowedDetailedProductionList,
                                                 allowedAutomaticProductionList, testResultDict)

    # depends on checkProductionTypesByRegex(), types are assigned there
    checkIfGenericVertexesAreAllowed(vertexList, allowedGenericProductionList, allowedCharactersList, allowedItemsList,
                                     allowedLocationsList, testResultDict)

    # CONNECTION-SPATIAL CHECK PART

    # depends on readEdgesAndVertexFromXml() main story props
    checkVertexAlignmentInMainStory(vertexList, mainStoryProps, testResultDict)

    checkIfVertexesAreIntersecting(vertexList, testResultDict)

    checkOutgoingEdgesCorrectness(vertexDict, edgeDict, testResultDict)

    startingChecks(vertexList, vertexDict, edgeList, edgeDict, testResultDict)

    checkIfAnyEndingFoundFromEveryVertex(vertexList, vertexDict, edgeDict, testResultDict, False)

    print("RESULTS\n\n")

    # for t in testResultDict.keys():
    #     print("\n\nFound in\n", t, ":\n")
    #     for e in testResultDict[t]:
    #         print("-", e)

    return testResultDict
