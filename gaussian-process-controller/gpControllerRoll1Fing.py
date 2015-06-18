import gp_controller as gpc
import iCubInterface
import numpy as np
import yarp
import time
import math
import random
import os
import find_lines

def exitModule(resetProbability):
    randomNum = random.random()
    if randomNum < resetProbability:
        return True
    return False

def logArray(array,fd):
    for i in range(len(array)):
        fd.write(str(array[i]))
        fd.write(" ")

def readValueFromFile(fileName):
    fd = open(fileName,"r")
    line = fd.readline().split()
    value = int(line[0])
    fd.close()
    return value

def writeIntoFile(fileName,string):
    fd = open(fileName,"w")
    fd.write(string)
    fd.close()

def addDescriptionData(dataString,parameter,value):
    dataString = dataString + parameter + " " + value + "\n"

def readImage(cameraPort,yarp_image):
    cameraPort.read(yarp_image)

def getFeedbackAngle(yarp_image,img_array):

    img_bgr = img_array[:,:,[2,1,0]]
    retList = find_lines.run_system2(img_bgr)
    first_line_polar = retList[3]
    theta = first_line_polar[1]
    return theta

def calculateFeedbackAngleDifference(previousFbAngle,currentFbAngle,fbAngleRange):

    delta = currentFbAngle - previousFbAngle

    if abs(delta) < fbAngleRange/2.0:
        fbAngleDifference = delta
    else:
        fbAngleDifference = np.sign(-delta)*(fbAngleRange - abs(delta))

    return fbAngleDifference

def findNewAngle(angle,alpha,beta):

    p1 = [1.0,0.0,0.0]
    p2 = [math.cos(angle),math.sin(angle),0.0]

    rx = [[1,0,0],[0,math.cos(alpha),-math.sin(alpha)],[0,math.sin(alpha),math.cos(alpha)]]
    ry = [[math.cos(beta),0,-math.sin(beta)],[0,1,0],[math.sin(beta),0,math.cos(beta)]]

    np1 = np.dot(ry,np.dot(rx,p1))
    np2 = np.dot(ry,np.dot(rx,p2))


def main():

    # module parameters
    maxIterations = [    77,    14,   134,    66,    10,    81,    22,    31,     3,    66]
    maxIterations2 = [    50,    14,   134,    66,    10,    81,    22,    31,     3,    66]

    proximalJointStartPos = 40
    distalJointStartPos = 0
    joint1StartPos = 18
    #                    0               1   2   3   4   5   6   7   8   9  10  11  12                    13                  14  15
    startingPosEncs = [-44, joint1StartPos, -4, 39,-14,  2,  2, 18, 12, 20,163,  0,  0,proximalJointStartPos,distalJointStartPos,  0]   
    
    actionEnabled = True

    rolloutsNumFirst = 30
    rolloutsNumStd = 10

    finger = 1
    proximalJoint = 13
    distalJoint = 14
    proximalJointEnc = 6
    distalJointEnc_1 = 7
    distalJointEnc_2 = 8

    resetProbability = 0.02

    actionDuration = 0.1
    pauseDuration = 0.0

    maxFbAngle = math.pi
    minFbAngle = 0
    maxFbAngleDifference = math.pi/3.0
    fbAngleRange = maxFbAngle - minFbAngle

    normalizedMaxVoltageY = 1.0
    maxVoltageProxJointY = 250.0
    maxVoltageDistJointY = 600.0
    slopeAtMaxVoltageY = 1.0

    waitTimeForFingersRepositioning = 7.0

    dataDumperPortName = "/gpc/log:i"
    iCubIconfigFileName = "iCubInterface.txt"
    inputFilePath = "./"
    initInputFileName = "controller_init.txt"
    standardInputFileName = "controller_input.txt"
    outputFilePath = "./"
    outputFileName = "controller_output.txt"
    dataPath = "./data/experiments/"
  
    jointsToActuate = [proximalJoint,distalJoint]
    
    fileNameIterID = "iterationID.txt"
    fileNameExpParams = "parameters.txt"

    # create output folder name
    expID = 16
    experimentFolderName = dataPath + "exp_" + str(expID) + "/" # could be changed adding more information about the experiment

    if os.path.exists(experimentFolderName):
        # get iteration ID
        iterID = readValueFromFile(fileNameIterID)        
        writeIntoFile(fileNameIterID,str(iterID+1))    
        inputFileFullName = inputFilePath + standardInputFileName
        rolloutsNum = rolloutsNumStd
    else:
        # create directory, create an experiment descrition file and reset iteration ID
        os.mkdir(experimentFolderName)
        descriptionData = ""
        descriptionData = descriptionData + "proximalJointMaxVoltage " + str(maxVoltageProxJointY) + "\n"
        descriptionData = descriptionData + "distalJointMaxVoltage " + str(maxVoltageDistJointY) + "\n"
        descriptionData = descriptionData + "slopeAtMaxVoltage " + str(slopeAtMaxVoltageY) + "\n"
        descriptionData = descriptionData + "actionDuration " + str(actionDuration) + "\n"
        descriptionData = descriptionData + "pauseDuration " + str(pauseDuration) + "\n"
        descriptionData = descriptionData + "finger " + str(finger) + "\n"
        descriptionData = descriptionData + "jointActuated " + str(proximalJoint) + " " + str(distalJoint) + "\n"
        descriptionData = descriptionData + "jointStartingPositions " + str(proximalJointStartPos) + " " + str(distalJointStartPos) + "\n"
        descriptionData = descriptionData + "resetProbabilty " + str(resetProbability) + "\n"
        descriptionData = descriptionData + "additionaNotes " + "" + "\n"
        writeIntoFile(experimentFolderName + fileNameExpParams,descriptionData)
        iterID = 0
        writeIntoFile(fileNameIterID,"1")
        inputFileFullName = inputFilePath + initInputFileName
        rolloutsNum = rolloutsNumFirst

    outputInputFileSuffix = str(expID) + "_" + str(iterID);
    backupOutputFileFullName = experimentFolderName + "contr_out_" + outputInputFileSuffix + ".txt"
    backupInputFileFullName = experimentFolderName + "contr_in_" + outputInputFileSuffix + ".txt"
    outputFileFullName = outputFilePath + outputFileName

    # calculate voltageX-voltageY mapping parameters (voltageY = k*(voltageX^(1/3)))
    k = pow(3*slopeAtMaxVoltageY*(pow(normalizedMaxVoltageY,2)),(1/3.0))

    maxVoltageX = pow(normalizedMaxVoltageY/k,3)

    # load gaussian process controller
    gp = gpc.GPController(inputFileFullName)
    gp.load_controller()

    # load iCub interface
    iCubI = iCubInterface.ICubInterface(dataDumperPortName,iCubIconfigFileName)
    iCubI.loadInterfaces()

    # cameras port
    cameraPort = yarp.Port()
    cameraPortName = "/gpc/leftEye"
    cameraPort.open(cameraPortName)
    yarp.Network.connect("/icub/cam/left",cameraPortName)

    # image setting
    width = 640
    height = 480 
    # Create numpy array to receive the image and the YARP image wrapped around it
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    yarp_image = yarp.ImageRgb()
    yarp_image.resize(width, height)
    yarp_image.setExternal(img_array, img_array.shape[1], img_array.shape[0])

    # set start position
    if actionEnabled:
        iCubI.setArmPosition(startingPosEncs)
        #iCubI.setRefVelocity(jointsToActuate,1000000)

    # wait for the user
    raw_input("- press enter to start the controller -")

    fd = open(outputFileFullName,"w")
    fd.write("nrollouts: ")
    fd.write(str(rolloutsNum))
    fd.write("\n")
    fd.close()
    
    # initialize velocity mode
    if actionEnabled:
        iCubI.setOpenLoopMode(jointsToActuate)

    rolloutsCounter = 0
    while rolloutsCounter < rolloutsNum:

        print "starting iteration n. ",rolloutsCounter + 1
        fd = open(outputFileFullName,"a")
        fd.write("# HEADER ")
        fd.write(str(rolloutsCounter + 1))
        fd.write("\n")

        iterCounter = 0
        exit = False
        voltage = [0,0]
        oldVoltage = [0,0]
        realVoltage = [0,0]
        readImage(cameraPort,yarp_image)
        currentFbAngle = getFeedbackAngle(yarp_image,img_array)
        # main loop
        while iterCounter < maxIterations[rolloutsCounter%10] and not exit:

            # read tactile data
            fullTactileData = iCubI.readTactileData()
            tactileData = []              
            for j in range(12):
                tactileData.append(fullTactileData.get(12*finger+j).asDouble())

            # read encoders data from port
            fullEncodersData = iCubI.readEncodersDataFromPort()
            encodersData = []
            encodersData.append(fullEncodersData.get(proximalJointEnc).asDouble())
            encodersData.append(fullEncodersData.get(distalJointEnc_1).asDouble())
            encodersData.append(fullEncodersData.get(distalJointEnc_2).asDouble())

            state = [tactileData,encodersData,voltage]

            # store image to be processed while action is applied
            readImage(cameraPort,yarp_image)

            # choose action
            action = gp.get_control(state)


            # update and cut voltage
            oldVoltage[0] = voltage[0]
            oldVoltage[1] = voltage[1]
            voltage[0] = voltage[0] + action[0];
            voltage[1] = voltage[1] + action[1];
            if abs(voltage[0]) > maxVoltageX:
                voltage[0] = maxVoltageX*np.sign(voltage[0])
            if abs(voltage[1]) > maxVoltageX:
                voltage[1] = maxVoltageX*np.sign(voltage[1])

            # calculate real applied voltage
            realVoltage[0] = maxVoltageProxJointY*k*pow(abs(voltage[0]),1/3.0)*np.sign(voltage[0])
            realVoltage[1] = maxVoltageDistJointY*k*pow(abs(voltage[1]),1/3.0)*np.sign(voltage[1])

            # voltage safety check (it should never happen!)
            if abs(realVoltage[0]) > maxVoltageProxJointY:
                realVoltage[0] = maxVoltageProxJointY*np.sign(realVoltage[0])
                print 'warning, voltage out of bounds!'
            if abs(realVoltage[1]) > maxVoltageDistJointY:
                realVoltage[1] = maxVoltageDistJointY*np.sign(realVoltage[1])
                print 'warning, voltage out of bounds!'


            # apply action
            if actionEnabled:
                iCubI.openLoopCommand(proximalJoint,realVoltage[0])        
                iCubI.openLoopCommand(distalJoint,realVoltage[1])

            # get feedback angle
            previousFbAngle = currentFbAngle
            beforeTS = time.time()
            currentFbAngle = getFeedbackAngle(yarp_image,img_array)
            fbAngleDifference = calculateFeedbackAngleDifference(previousFbAngle,currentFbAngle,fbAngleRange)
            if abs(fbAngleDifference > maxFbAngleDifference):
                currentFbAngle = previousFbAngle
                fbAngleDifference = 0.0
            afterTS = time.time()
            timeToSleep = max(actionDuration-(afterTS-beforeTS),0)
            time.sleep(timeToSleep)


#            print "curr ",previousFbAngle*180/3.1415,"diff ",fbAngleDifference*180/3.1415,afterTS - beforeTS,timeToSleep


            # wait for stabilization
            time.sleep(pauseDuration)
 
            print oldVoltage[0],oldVoltage[1],action[0],action[1]
            # log data
            iCubI.logData(tactileData + encodersData + oldVoltage + [action[0],action[1]])
            logArray(tactileData,fd)
            logArray(encodersData,fd)
            logArray(oldVoltage,fd)
            logArray(action,fd)
            logArray([fbAngleDifference],fd)
            fd.write("\n")

            #print 'prev ',previousFbAngle*100/3.1415,'curr ',currentFbAngle*100/3.1415,'diff ',fbAngleDifference*100/3.1415


            iterCounter = iterCounter + 1
            exit = False #exitModule(resetProbability)

        fd.close()

        if actionEnabled:
            print "finger ripositioning..."
            # finger repositioning
            iCubI.setPositionMode(jointsToActuate)
            iCubI.setJointPosition(1,joint1StartPos + 5)
            time.sleep(1)
            iCubI.setJointPosition(proximalJoint,proximalJointStartPos)
            iCubI.setJointPosition(distalJoint,distalJointStartPos)
            time.sleep(2)
            iCubI.setJointPosition(1,joint1StartPos)
            time.sleep(1)
            iCubI.setOpenLoopMode(jointsToActuate)


#            iCubI.setPositionMode(jointsToActuate)
#            iCubI.setJointPosition(proximalJoint,0.0)
#            iCubI.setJointPosition(distalJoint,0.0)
#            time.sleep(waitTimeForFingersRepositioning)
#            iCubI.setJointPosition(proximalJoint,proximalJointStartPos)
#            iCubI.setJointPosition(distalJoint,distalJointStartPos)
#            time.sleep(waitTimeForFingersRepositioning)
#            iCubI.setOpenLoopMode(jointsToActuate)
            print "...done"


        rolloutsCounter = rolloutsCounter + 1
            
    os.system("cp " + inputFileFullName + " " + backupInputFileFullName)
    os.system("cp " + outputFileFullName + " " + backupOutputFileFullName)

    # copy input and output file
    # restore position mode and close iCubInterface
    if actionEnabled:
        iCubI.setPositionMode(jointsToActuate)
    cameraPort.close()
    iCubI.closeInterface()
    
		
if __name__ == "__main__":
    main()
