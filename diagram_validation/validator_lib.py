
import xml.etree.ElementTree as ET
import re
from html.parser import HTMLParser
from collections import defaultdict
from functools import reduce
import json
import sys
from typing import List
import os



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
    def __init__(self, id, content, prodType, color, xPosition, yPosition,vWidth):
        self.id = id
        self.content = content
        self.prodType = prodType
        self.color = color
        self.x = xPosition
        self.y = yPosition
        self.width = vWidth

    def show(self):
        print("Vertex:","\n\tid:", self.id,"\tid:", self.id,"\n\tcontent:", self.content,"\n\ttype:", self.prodType, "\n\tcolor",self.color,"\n\txPos:",self.x,"\n\tyPos:",self.y)

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
            isDetailedProductionAllowed(x.content,allowedDetailedProductionList, testResultDict)





def isDetailedProductionAllowed(production, detailedProductionList, testResultDict):
    """
    checks if production is on allowed json list, by comparing name
    :param vertexList: string name of production, format. Eng name / Pl name
    :param allowedDetailedProductionList: allowed productions list, read from json
    :param testResultDict: reference for test dict
    """
    isOnList = False
    # print("val prod",production)
    for p in detailedProductionList:
        # print(production,"\n",p["Title"],"\n", p["Title"]==production,"\n")
        if p["Title"].strip() == production.strip():
            isOnList = True
    # print("\n")
    if not isOnList:
        if production not in testResultDict:
            testResultDict[production] =[]

        testResultDict[production].append("ERROR\n\t" +production + "\n\tDetailed production was not found on allowed detailed productions list, check for spelling mistakes")

        # testResultDict.append("ERROR\n\t" +production + "\n\tDetailed production was not found on allowed detailed productions list, check for spelling mistakes" )


def isGenericProductionAllowed(production,genericProductionList, charactersList,itemsList,locationsList, testResultDict):
    """
    checks if production is on allowed json list, by comparing name,
    checks if arguments in brackets are on one of allowed lists,
    counts and checks number of arguments

    :param production: string name of production, format. Eng name / Pl name; (Arg, Arg)
    :param genericProductionList: allowed generic productions, read from json
    :param charactersList: allowed characters list
    :param itemsList: allowed items list
    :param locationsList: allowed locations list
    :param testResultDict: reference for test dict

    :return Boolean
    """
    begIndex = 0
    if production[0] == " ":
        begIndex = 1

    semicolonIndex = production.find(";")

    if production[semicolonIndex] ==" ":
        semicolonIndex -=1

    titlePart = production[begIndex:semicolonIndex]
    isOnList = False

    for p in genericProductionList:
        if p["Title"] == titlePart:

            isOnList = True

    if not isOnList:
        if production not in testResultDict:
            testResultDict[production] =[]


        if "`" in production or "'" in production:
            testResultDict[production].append("ERROR\n\t" +production + "\n\tGeneric production was not found on allowed generic productions list, check for accidental ' apostrophes, (maybe ’)")

        else:
            testResultDict[production].append("ERROR\n\t" +production + "\n\tGeneric production was not found on allowed generic productions list, check for spelling mistakes" )

        return False


    bracketPart = production[semicolonIndex+1:]
    bracketPart = bracketPart.strip()

    argsInBrackets = separateArgsFromBrackets(bracketPart)

    # for arg in argsInBrackets:
    #     if (arg not in charactersList) and (arg not in itemsList) and (arg not in locationsList) :
    #         if "/" in arg:
    #             slashArgs = arg.split('/')
    #             areSlashArgsCorrect = True
    #             # print(slashArgs)
    #             for sa in slashArgs:
    #                 if (sa not in charactersList) and (sa not in itemsList) and (sa not in locationsList):
    #                     # zamiast errora - slashe

    #                     testResultDict[production].append("ERROR\n\t" +production+"\n\tIn arg: " +arg+", this arg " + sa + " was not found on Characters/Items/Locations list, check for spelling mistakes")
    #             #
    #         else:
    #             if production not in testResultDict:
    #                 testResultDict[production] =[]
    #             testResultDict[production].append("ERROR\n\t" +production + "\n\t"+arg+" is not on allowed Characters/Items/Locations list, check for spelling mistakes, Ignore if its narration element")

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

    print("!!")
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
                    print(i)
                    if "Id" in i:
                        charactersCount += 1

                    if("Items" in  i ):
                        itemsCount += len(i["Items"])
                        for it in i["Items"]:
                            print(i)

                    if ("Narration" in i):
                        narrationCount +=1



            if "Location change" in production:
                if(argsCount == 2):
                    return True
            if "Picking item" in production or "Dropping item" in production:
                if(argsCount == 1):
                    return True

            if charactersCount + itemsCount + connectionsCount + narrationCount != argsCount:
                if production not in testResultDict:
                    testResultDict[production] =[]
                if argsCount == 1:
                    testResultDict[production].append("WARNING\n\t" +production+"\n\tCheck amount of args in production " )

                elif "Location change" in production:
                    testResultDict[production].append("WARNING\n\t" +production+"\n\tCheck amount of args in production " )
                else:
                    testResultDict[production].append("WARNING\n\t" +production+"\n\tCheck amount of args in production, expected " + str(charactersCount + itemsCount + connectionsCount + narrationCount) + ", but got " + str(argsCount) )

    for arg in argsInBrackets:
        if (arg not in charactersList) and (arg not in itemsList) and (arg not in locationsList) :
            if "/" in arg:
                slashArgs = arg.split('/')
                areSlashArgsCorrect = True
                # print(slashArgs)
                for sa in slashArgs:
                    if (sa not in charactersList) and (sa not in itemsList) and (sa not in locationsList):
                        # zamiast errora - slashe

                        testResultDict[production].append("ERROR\n\t" +production+"\n\tIn arg: " +arg+", this arg " + sa + " was not found on Characters/Items/Locations list, check for spelling mistakes")
                #
            else:
                if production not in testResultDict:
                    testResultDict[production] =[]
                if narrationCount > 0:
                    testResultDict[production].append("WARNING\n\t" +production + "\n\t"+arg+" is not on allowed Characters/Items/Locations list, Narration element was detected, Ignore if its narration")
                else:
                    testResultDict[production].append("ERROR\n\t" +production + "\n\t"+arg+" is not on allowed Characters/Items/Locations list, check for spelling mistakes")


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





def readEdgesAndVertexFromXml(drawingFileLocation, vertexListToFill, edgeListToFill, edgeDictToFill, mainStoryPropsToFill, testResultDict, notAllowedShapesList):
    """
    Fills vertex list, edge list, edge dictionary, main story positional properties and test result list
    Should be used first, to load from XML correctly

    :param drawingFileLocation: path to drawing XML file
    :param vertexListToFill: empty list reference, to be filled with Vertex entities
    :param edgeListToFill: empty list reference, to be filled with edge entities
    :param edgeDictToFill: empty default dictionary reference, to be filled with edge entities
    :param mainStoryPropsToFill: Entity of MainStoryProps
    :param testResultDict: dict to store test results
    :param notAllowedShapesList: list to be passed for checks, take it from constants at top of file
    """
    tree = ET.parse(drawingFileLocation)
    root = tree.getroot()
    parser = MyHTMLParser()
    mainStoryWidth= 0


    endingProductionType = "ending"

    for elem in root.iter('mxCell'):
        if "edge" in elem.attrib:

            if(("source" not in elem.attrib ) or ("target" not in elem.attrib)):
                if elem.attrib["id"] not in testResultDict:
                    testResultDict[elem.attrib["id"]] =[]
                print("ea ",elem)
                edge_x = 0
                edge_y = 0
                for geometry in elem.iter('mxGeometry'):
                    for point in geometry.iter('mxPoint'):
                        edge_x = point.attrib["x"]
                        edge_y = point.attrib["y"]


                testResultDict[elem.attrib["id"]].append(
                    'ERROR\n\tedge with id ' + str(elem.attrib["id"]) +"\n\tis not connected to source or target properly, coordinates: (" + str(edge_x) + "," + str(edge_y) +")"
                )
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
                    if str(s) not in testResultDict:
                        testResultDict[str(s)] =[]
                    testResultDict[str(s)].append("ERROR\n\t"+str(s)+" vertex shape is not allowed, skipping this vertex in checkups")
                    foundAtLeastBadOneVertex = True
                    continue





            if "ellipse" in elem.attrib["style"]:

                if "value" in elem.attrib and not elem.attrib["id"] == "":
                    if( bool(re.search("\s?[1-9][0-9]?\s?",elem.attrib["value"]))):
                        vertexListToFill.append(
                            Vertex(elem.attrib["id"],
                                   elem.attrib["value"].replace("<br>","\n"),
                                   endingProductionType,
                                   parseColor(elem.attrib["style"]),
                                   0,
                                   0,
                                   0
                                   ))
                else:
                    if str( elem.attrib["id"]) not in testResultDict:
                        testResultDict[ str( elem.attrib["id"])] =[]
                    testResultDict[ str( elem.attrib["id"])].append('ERROR\n\t'+'check id: '+ str( elem.attrib["id"])+'\n\tUnexpected value in ending production (not a mission number)')



                vertexListToFill.append(
                    Vertex(elem.attrib["id"],
                           "",
                           endingProductionType,
                           parseColor(elem.attrib["style"]),
                           0,
                           0,
                           0
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

            if not (hasX and hasY and hasWidth):
                hasX=False
                hasY=False
                hasWidth = False
                foundAtLeastBadOneVertex = True
                if str(elem.attrib["value"]) not in testResultDict:
                    testResultDict[ str(elem.attrib["value"])] =[]

                testResultDict[ str(elem.attrib["value"])].append('ERROR\n\t'+str(elem.attrib["value"]) + '\n\tis not proper vertex, has no x or y position or no width, skipping this vertex in later checkups')
                continue


            vertexListToFill.append(
                Vertex(elem.attrib["id"],
                       reduce(lambda a,b: a+b,parser.return_data()),
                       "type",
                       parseColor(elem.attrib["style"]),
                       float(xPos),
                       float(yPos),
                       float(width)
                       )
            )

            continue

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
                    if str(x.content) not in testResultDict:
                        testResultDict[str(x.content)] =[]
                    testResultDict[str(x.content)].append("WARNING\n\t" + str(x.content) +"\n\tCheck if vertexes are alligned in main story")

# def checkIfVertexesAreIntersecting(vertexList:List[Vertex],testResultDict):

"""
TO FINISH
"""


#     endingProductionType = "ending"
#     for v in vertexList:
#         if v.prodType != endingProductionType:
#             for v2 in vertexList:
#                 if( (v != v2) and v2.prodType != endingProductionType):
#                     v.show()
#                     if (v.x + v.width > v2.x ) and (v.y)



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
            if str(x.content) not in testResultDict:
                testResultDict[str(x.content)] =[]
            testResultDict[str(x.content)].append("ERROR\n\t"+str(x.content)+"\n\tProduction name does not seem to fit any proper format of production, check '!'")

        elif( x.prodType != endingProductionType):
            if str(x.content) not in testResultDict:
                testResultDict[str(x.content)] =[]
            testResultDict[str(x.content)].append("ERROR\n\t"+str(x.content)+"\n\tProduction name does not seem to fit any proper format of production")


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
            if str(x.content) not in testResultDict:
                testResultDict[str(x.content)] =[]
            testResultDict[str(x.content)].append("WARNING\n\t"+ x.content + "\n\tSkipped color check as production type was not recognized")

        elif not isVertexColorCorrect(x,vertexTypesList,allowedColorDictionary) and (x.color.lower() in allowedColorDictionary[genericProductionType] ):
            if str(x.content) not in testResultDict:
                testResultDict[str(x.content)] =[]
            testResultDict[str(x.content)].append("WARNING\n\t" +x.content+"\n\tfound color in production: " + x.color+", make sure its generic production(generic colors are none or #ffffff). If it is, ignore warning")

        elif not isVertexColorCorrect(x,vertexTypesList,allowedColorDictionary):
            if str(x.content) not in testResultDict:
                testResultDict[str(x.content)] =[]
            testResultDict[str(x.content)].append("ERROR\n\t" +x.content+"\n\tcolor " + x.color+" in production of type "+x.prodType +" is not on allowed list: " + str(allowedColorDictionary[x.prodType]))


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
            isGenericProductionAllowed(x.content,allowedGenericProductionList,charactersList, itemsList, locationsList, testResultDict)


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
                if str(v.content) not in testResultDict:
                    testResultDict[str(v.content)] =[]
                testResultDict[str(v.content)].append("ERROR\n\t"+str(v.content)+"\n\tNo outgoing edges from non-ending vertex")

        if bool(edgeDict.get(v.id)) and v.prodType == endingProductionType:
            if str(v.id) not in testResultDict:
                testResultDict[str(v.id)] =[]
            testResultDict[str(v.id)].append("ERROR\n\t"+"ending id"+str(v.id)+"\n\tending should not have outgoing edges")

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
        if "START" not in testResultDict:
            testResultDict["START"] =[]
        testResultDict["START"].append("ERROR\n\t","Could not find staring point, make sure that it is higher than any vertex pointing to it or has no incoming edges")


    if(len(suspectedStartingVertex) > 1):
        if "START" not in testResultDict:
            testResultDict["START"] =[]
        testResultDict["START"].append("WARNING\n\t"+"more than one vertex is a starting point (no incoming edges or its higher than all incoming edges), please check if there should be more than one starting points")


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
                    if v.content not in testResultDict:
                        testResultDict[v.content] =[]
                    testResultDict[v.content].append(
                        "ERROR\n\t"+
                        v.content +
                        '\n\tCould not reach any ending from vertex, check connections'
                    )
    else:
        if "SKIPPED ENDING SEARCH" not in testResultDict:
            testResultDict["SKIPPED ENDING SEARCH"] =[]
        testResultDict["SKIPPED ENDING SEARCH"].append(
            "WARNING\n\t"+
            'Skipped ending search from each vertex'
        )