from validator_lib import *

missionProductionType= "mission"
genericProductionType = "generic"
detailedProductionType = "detailed"
endingProductionType = "ending"
allowedColorDictionary = defaultdict()
allowedColorDictionary[missionProductionType] ="#e1d5e7"
allowedColorDictionary[genericProductionType] = {"#ffffff","none"}
allowedColorDictionary[detailedProductionType] ="#d5e8d4"
allowedColorDictionary[endingProductionType] = {"#fff2cc","#000000","#ffffff","#e1d5e7","none","none;"}


vertexList =[]
vertexDict = defaultdict()
edgeList =[]
edgeDict = defaultdict()
testResultDict = defaultdict()


notAllowedShapesList =["rhombus", "process","parallelogram", "hexagon","cloud"]
allowedGenericProductionList = loadFromJson(os.curdir + os.sep +"produkcje_generyczne.json")
allowedCharactersList= loadFromJson(os.curdir + os.sep +"allowedCharacters.json")
allowedItemsList = loadFromJson(os.curdir + os.sep +"allowedItems.json")
allowedLocationsList= loadFromJson(os.curdir + os.sep +"allowedLocations.json")
allowedDetailedProductionList = loadFromJson(os.curdir + os.sep +sys.argv[2])
# print(allowedDetailedProductionList)

mainStoryProps = MainStoryProps(0,0,0,0,0,0)

if len(sys.argv) == 1:
    print("please pass name of xml file to verify in cli argument, ex:\n\t",
          "python3 validator_new.py example.drawio.xml"
          )
    exit(-1)

pathToXml =  os.curdir + os.sep + sys.argv[1]


# LOADING PART

readEdgesAndVertexFromXml(pathToXml,vertexList,edgeList,edgeDict, mainStoryProps,testResultDict,notAllowedShapesList)

copyVertexListToDict(vertexList,vertexDict)

checkProductionTypesByRegex(vertexList,testResultDict) # nadaje typ produkcji udok




# TYPE RELATED CHECK PART
# depends on checkProductionTypesByRegex(), types are assigned there
checkVertexListColors(vertexList,testResultDict,allowedColorDictionary)

# depends on checkProductionTypesByRegex(), types are assigned there
checkIfDetailedVertexesAreAllowed(vertexList,allowedDetailedProductionList,testResultDict)

# depends on checkProductionTypesByRegex(), types are assigned there
checkIfGenericVertexesAreAllowed(vertexList,allowedGenericProductionList,allowedCharactersList,allowedItemsList,allowedLocationsList,testResultDict)





# CONNECTION-SPATIAL CHECK PART

# depends on readEdgesAndVertexFromXml() main story props
checkVertexAlignmentInMainStory(vertexList,mainStoryProps,testResultDict)

# checkIfVertexesAreIntersecting(vertexList,testResultDict)

checkOutgoingEdgesCorrectness(vertexDict,edgeDict,testResultDict)

startingChecks(vertexList,vertexDict,edgeList,edgeDict,testResultDict)

checkIfAnyEndingFoundFromEveryVertex(vertexList,vertexDict,edgeDict,testResultDict,False)


print("RESULTS\n\n")


for t in testResultDict.keys():
    print("\n\nFound in\n",t,":\n")
    for e in testResultDict[t]:
        print("-",e)

