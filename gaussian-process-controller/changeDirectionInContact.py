import iCubInterface
import numpy as np
import yarp
import time
import sys

def doTask(jointToMove,actionSteps,pauseSteps,pwmStep,raiseSteps,logEnabled,iCubI,fd):

    fullEncodersData = iCubI.readEncodersData()
    startingEncoderValue = fullEncodersData[jointToMove]

    encoderValue = startingEncoderValue

    iterCounter = 0
    while iterCounter < maxIterations:

        if iterCounter < raiseSteps:
            voltage = (iterCounter + 1)*pwmStep
        currentTarget = encoderValue + angleStep;
        intIterCounter = 0
        while intIterCounter < actionSteps:

            fullEncodersData = iCubI.readEncodersData()
            encoderValue = fullEncodersData[jointToMove]

            pwmToUse = kpGain*scale*(currentTarget - encoderValue)
            if pwmToUse > maxVoltage:
                pwmToUse = maxVoltage
            elif pwmToUse < -maxVoltage:
                pwmToUse = -maxVoltage
            iCubI.openLoopCommand(jointToMove,pwmToUse)

            if logEnabled:
                fd.write(str(iterCounter*0.10))
                fd.write(" ")
                fd.write(str(encoderValue-startingEncoderValue))
                fd.write(" ")
                fd.write(str(currentTarget-startingEncoderValue))
                fd.write(" ")
                fd.write(str((iterCounter+1)*angleStep))
                fd.write(" ")
                fd.write(str(pwmToUse))
                fd.write("\n")

            intIterCounter = intIterCounter + 1

            time.sleep(0.01)

        iterCounter = iterCounter + 1

    iCubI.openLoopCommand(jointToMove,0.0)

    if iterCounter == maxIterations:
        print 'reaching ',targetPos,' failed'
        sys.exit()




def main():

    # module parameters
    dataDumperPortName = "/gpc/log:i"
    iCubIconfigFileName = "iCubInterface"
    jointToMove = 13
    # startinPosition1 < targetPosition < startingPosition2
    startingPosition = 30
    actionSteps = 20
    pauseSteps = 5
    pwmStep = 50
    raiseSteps = 6    

    fileName = "tactileCD_A" + str(actionSteps) + "_P" + str(pauseSteps) + "_V" + str(pwmStep) + ".txt"; 
    fd = open(fileName,"w")

    # load iCub interface
    iCubI = iCubInterface.ICubInterface(dataDumperPortName,iCubIconfigFileName)
    iCubI.loadInterfaces()

    # set position mode
    iCubI.setPositionMode([jointToMove])

    # put finger in startingPosition1
    iCubI.setJointPosition(jointToMove,startingPosition1)

    # wait for the user
    raw_input("- press enter to move the finger -")

    # initialize open loop mode
    iCubI.setOpenLoopMode([jointToMove])

    # move finger from startingPosition1 to targetPosition
    doTask(jointToMove,actionSteps,pauseSteps,pwmStep,raiseSteps,True,iCubI,fd)

    fd.close()

    # restore position mode and close iCubInterface
    iCubI.setPositionMode([jointToMove])
    iCubI.closeInterface()
 
		
if __name__ == "__main__":
    main()