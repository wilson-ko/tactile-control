import gp_controller as gpc
import iCubInterface
import numpy as np
import yarp
import time

def exitModule(state):
   
    # TODO
    return False

def main():

    # module parameters
    maxIterations = 10000
    rolloutsNum = 15
    #                    0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15 
    startingPosEncs = [-44, 18, -4, 39,-14,  2,  2, 18, 12, 20,163,  0,  0, 40,  0,  0]   
    
    finger = 1
    proximalJoint = 13
    distalJoint = 14
    proximalJointEnc = 6
    distalJointEnc_1 = 7
    distalJointEnc_2 = 8

    actionDuration = 0.1
    pauseDuration = 0.0

    stictionVoltage = 100
    
    dataDumperPortName = "/gpc/log:i"
    iCubIconfigFileName = "iCubInterface"
    gpConfigFileSuffix = "_example"
  
    jointsToActuate = [proximalJoint,distalJoint]
    
    # load gaussian process controller
    gp = gpc.GPController(gpConfigFileSuffix)
    gp.load_controller()

    # load iCub interface
    iCubI = iCubInterface.ICubInterface(dataDumperPortName,iCubIconfigFileName)
    iCubI.loadInterfaces()

    # set start position
#    iCubI.setArmPosition(startingPosEncs)

    # wait for the user
    raw_input("- press enter to start the controller -")

    # initialize velocity mode
#    iCubI.setOpenLoopMode(jointsToActuate)

    rolloutsCounter = 0
    while rolloutsCounter < rolloutsNum

        iterCounter = 0
        exit = False
        voltage = [0,0]
        # main loop
        while iterCounter < maxIterations and not exit:

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

            # choose action
            action = gp.get_control(state)

            voltage[0] = voltage[0] + action[0];
            voltage[1] = voltage[1] + action[1];

            # log data
            iCubI.logData(tactileData + encodersData + voltage + [action[0],action[1]])

            print state,action

            # apply action
#            iCubI.openLoopCommand(proximalJoint,voltage[0])        
#            iCubI.openLoopCommand(distalJoint,voltage[1])        
            time.sleep(actionDuration)

            # wait for stabilization
            time.sleep(pauseDuration)
 
            iterCounter = iterCounter + 1
            exit = exitModule(state)

      rolloutsCounter = rolloutsCounter + 1
            

    # restore position mode and close iCubInterface
#    iCubI.setPositionMode(jointsToActuate)
    iCubI.closeInterface()
 
		
if __name__ == "__main__":
    main()
