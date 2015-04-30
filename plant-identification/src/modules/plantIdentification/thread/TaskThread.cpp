#include "iCub/plantIdentification/thread/TaskThread.h"
#include "iCub/plantIdentification/task/StepTask.h"
#include "iCub/plantIdentification/task/ControlTask.h"
#include "iCub/plantIdentification/task/ApproachTask.h"
#include "iCub/plantIdentification/task/RampTask.h"

#include <yarp/os/Property.h>
#include <yarp/os/Network.h>
#include <yarp/os/Time.h>

#include <iostream>
#include <sstream>
#include <algorithm>
#include <ctime>
#include <cmath>

using std::cerr;
using std::cout;
using std::string;

using iCub::plantIdentification::TaskThread;
using iCub::plantIdentification::RPCSetCmdArgName;
using iCub::plantIdentification::RPCTaskCmdArgName;
using iCub::plantIdentification::TaskName;
using iCub::plantIdentification::RPCViewCmdArgName;
using iCub::plantIdentification::RPCCommandsData;

using yarp::os::RateThread;
using yarp::os::Value;


/* *********************************************************************************************************************** */
/* ******* Constructor                                                      ********************************************** */   
TaskThread::TaskThread(const int period, const yarp::os::ResourceFinder &aRf) 
    : RateThread(period) {
		this->period = period;
        rf = aRf;

        dbgTag = "TaskThread: ";
}
/* *********************************************************************************************************************** */


/* *********************************************************************************************************************** */
/* ******* Destructor                                                       ********************************************** */   
TaskThread::~TaskThread() {}
/* *********************************************************************************************************************** */


/* *********************************************************************************************************************** */
/* ******* Initialise thread                                                ********************************************** */
bool TaskThread::threadInit() {
    using yarp::os::Property;
    using yarp::os::Network;
    using yarp::os::Bottle;
    using yarp::os::Time;
    using std::vector;

	cout << dbgTag << "Initialising. \n";

	currentTaskIndex = 0;

	// initialize controllers
	controllersUtil = new ControllersUtil();
	if (!controllersUtil->init(rf)) {
        cout << dbgTag << "failed to initialize controllers utility\n";
        return false;
    }

	// initialize ports
	portsUtil = new PortsUtil();
	if (!portsUtil->init(rf)) {
        cout << dbgTag << "failed to initialize ports utility\n";
        return false;
    }
	// initialize task data
	taskData = new TaskData(rf,period);

	// save current arm position, to be restored when the thread ends
//	if (!controllersUtil->saveCurrentArmPosition()) {
//        cout << dbgTag << "failed to store current arm position\n";
//        return false;
//    }
//	if (!controllersUtil->setArmInTaskPosition()) {
//        cout << dbgTag << "failed to set arm in task position\n";
//        return false;
//    }
 
	// this prevent the run() method to be executed between the taskThread->start() and the taskThread->suspend() calls during the PlantIdentificationModule initialization
	runEnabled = false;

    cout << dbgTag << "Initialised correctly. \n";

    return true;
}
/* *********************************************************************************************************************** */


bool TaskThread::initializeGrasping(){

	if (!controllersUtil->saveCurrentControlMode()) return false;
	runEnabled = true;

	return true;
}


/* *********************************************************************************************************************** */
/* ******* Run thread                                                       ********************************************** */
void TaskThread::run() {

	if (runEnabled){

		if (currentTaskIndex < taskList.size()){

			// if it is the last task of the list, keep it active until further tasks are added
			bool keepActive = (currentTaskIndex == taskList.size() - 1);
			bool taskIsActive;

			taskIsActive = taskList[currentTaskIndex]->manage(keepActive);

			if (!taskIsActive){
				currentTaskIndex++;
			}
		}
	}
}

bool TaskThread::afterRun(bool openHand){

	if (!controllersUtil->restorePreviousControlMode()) return false;
	if (openHand) {
		if (!controllersUtil->openHand()) return false;
	}
	runEnabled = false;
    currentTaskIndex = 0;

	// clear task list
	for (size_t i = 0; i < taskList.size(); i++){
		delete(taskList[i]);
	}
	taskList.clear();

	return true;
}

/* *********************************************************************************************************************** */
/* ******* Release thread                                                   ********************************************** */
void TaskThread::threadRelease() {
    cout << dbgTag << "Releasing. \n";
    
    // closing ports
	portsUtil->release();

//    controllersUtil->restorePreviousArmPosition();
	controllersUtil->release();

	delete(portsUtil);
	delete(controllersUtil);
	delete(taskData);

    cout << dbgTag << "Released. \n";
}
/* *********************************************************************************************************************** */

bool TaskThread::setArmInTaskPosition(){

	if (!controllersUtil->setArmInTaskPosition()) {
        cout << dbgTag << "failed to set arm in task position\n";
        return false;
    }

    return true;

}

void TaskThread::set(RPCSetCmdArgName paramName,Value paramValue,RPCCommandsData &rpcCmdData){

	bool setSuccessful = true;

	switch (paramName){

	// common data
	case PWM_SIGN:
		taskData->commonData.pwmSign = paramValue.asInt();
		break;
	case OBJ_DETECT_PRESS_THRESHOLDS:
		rpcCmdData.setValues(paramValue.asString(),taskData->commonData.objDetectPressureThresholds);
		break;

	// step task data
	case STEP_LIFESPAN:
		taskData->stepData.lifespan = paramValue.asDouble();
		break;

	// control task data
	case CTRL_PID_KPF:
		rpcCmdData.setValues(paramValue.asString(),taskData->controlData.pidKpf);
		break;
	case CTRL_PID_KIF:
		rpcCmdData.setValues(paramValue.asString(),taskData->controlData.pidKif);
		break;
	case CTRL_PID_KPB:
		rpcCmdData.setValues(paramValue.asString(),taskData->controlData.pidKpb);
		break;
	case CTRL_PID_KIB:
		rpcCmdData.setValues(paramValue.asString(),taskData->controlData.pidKib);
		break;
	case CTRL_PID_RESET_ENABLED:
		taskData->controlData.pidResetEnabled = paramValue.asInt() != 0;
		break;
	case CTRL_OP_MODE:
		taskData->controlData.controlMode = static_cast<ControlTaskOpMode>(paramValue.asInt());
		break;
	case CTRL_TARGET_REAL_TIME:
		if (currentTaskIndex < taskList.size()){
			if (ControlTask* currentTask = dynamic_cast<ControlTask*>(taskList[currentTaskIndex])){
				std::vector<double> targetList;
				rpcCmdData.setValues(paramValue.asString(),targetList);
				currentTask->setTargetListRealTime(targetList);
			} else {
				setSuccessful = false;
				cout << "\n\n" << "CANNOT EXECUTE SET COMMAND (CONTROL TASK IS NOT RUNNING)" << "\n";
			}
		} else {
			setSuccessful = false;
			cout << "\n\n" << "CANNOT EXECUTE SET COMMAND (NO TASK RUNNING)" << "\n";
		}
		break;
	case CTRL_LIFESPAN:
		taskData->controlData.lifespan = paramValue.asInt();
		break;

	// ramp task data
	case RAMP_SLOPE:
		taskData->rampData.slope = paramValue.asDouble();
		break;
	case RAMP_INTERCEPT:
		taskData->rampData.intercept = paramValue.asDouble();
		break;
	case RAMP_LIFESPAN:
		taskData->rampData.lifespan = paramValue.asInt();
		break;
	case RAMP_LIFESPAN_AFTER_STAB:
		taskData->rampData.lifespanAfterStabilization = paramValue.asInt();
		break;

	// approach task data
	case APPR_JOINTS_VELOCITIES:
		rpcCmdData.setValues(paramValue.asString(),taskData->approachData.velocitiesList);
		break;
	case APPR_JOINTS_PWM_LIMITS:
		rpcCmdData.setValues(paramValue.asString(),taskData->approachData.jointsPwmLimitsList);
		break;
	case APPR_JOINTS_PWM_LIMITS_ENABLED:
		taskData->approachData.jointsPwmLimitsEnabled = paramValue.asInt() != 0;
		break;
	case APPR_LIFESPAN:
		taskData->approachData.lifespan = paramValue.asInt();
		break;


	}

	if (setSuccessful){
		cout << "\n" <<
				"\n" << 
				"'" << rpcCmdData.setCmdArgMap[paramName] << "' SET TO " << rpcCmdData.printValue(paramValue) << "\n";
	}
}

void TaskThread::task(RPCTaskCmdArgName paramName,TaskName taskName,Value paramValue,RPCCommandsData &rpcCmdData){

	std::vector<double> targetList;

	switch (paramName){

	case ADD:

		rpcCmdData.setValues(paramValue.asString(),targetList);

		switch (taskName){
		case STEP:
			taskList.push_back(new StepTask(controllersUtil,portsUtil,&taskData->commonData,&taskData->stepData,targetList));
			break;

		case CONTROL:
			taskList.push_back(new ControlTask(controllersUtil,portsUtil,&taskData->commonData,&taskData->controlData,targetList));
			break;

		case APPROACH_AND_CONTROL:
			taskList.push_back(new ControlTask(controllersUtil,portsUtil,&taskData->commonData,&taskData->controlData,targetList,true));
			break;

		case APPROACH:
			taskList.push_back(new ApproachTask(controllersUtil,portsUtil,&taskData->commonData,&taskData->approachData));
			break;

		case RAMP:
			taskList.push_back(new RampTask(controllersUtil,portsUtil,&taskData->commonData,&taskData->rampData,targetList));
			break;
		}
		cout << "\n" <<
				"\n" << 
				"ADDED '" << rpcCmdData.taskMap[taskName] << "' TASK" << "\n";
		break;

	case EMPTY:
		for (size_t i = 0; i < taskList.size(); i++){
			delete(taskList[i]);
		}
		taskList.clear();
		cout << "\n" <<
				"\n" << 
				"'" << "TASK LIST CLEARED" << "\n";
		break;

	case POP:
		delete(taskList[taskList.size() - 1]);
		taskList.pop_back();
		cout << "\n" <<
				"\n" << 
				"'" << "LAST TASK REMOVED" << "\n";
		break;
	}
}

void TaskThread::view(RPCViewCmdArgName paramName,RPCCommandsData &rpcCmdData){

	switch (paramName){

	case SETTINGS:
		cout << "\n" <<
		        "\n" <<
                "-------- SETTINGS --------" << "\n" <<
		        "\n" <<
		        "--- TASK COMMON DATA -----" << "\n" <<
		        rpcCmdData.getFullDescription(PWM_SIGN) << ": " << taskData->commonData.pwmSign << "\n" <<
				rpcCmdData.getFullDescription(OBJ_DETECT_PRESS_THRESHOLDS) << ": " << taskData->getValueDescription(OBJ_DETECT_PRESS_THRESHOLDS) << "\n" <<
		        "\n" <<
		        "--- STEP TASK DATA -------" << "\n" <<
		        rpcCmdData.getFullDescription(STEP_LIFESPAN) << ": " << taskData->stepData.lifespan << "\n" <<
		        "\n" <<
		        "--- CONTROL TASK DATA ----" << "\n" <<
				rpcCmdData.getFullDescription(CTRL_PID_KPF) << ": " << taskData->getValueDescription(CTRL_PID_KPF) << "\n" <<
		        rpcCmdData.getFullDescription(CTRL_PID_KIF) << ": " << taskData->getValueDescription(CTRL_PID_KIF) << "\n" <<
		        rpcCmdData.getFullDescription(CTRL_PID_KPB) << ": " << taskData->getValueDescription(CTRL_PID_KPB) << "\n" <<
		        rpcCmdData.getFullDescription(CTRL_PID_KIB) << ": " << taskData->getValueDescription(CTRL_PID_KIB) << "\n" <<
		        rpcCmdData.getFullDescription(CTRL_OP_MODE) << ": " << taskData->controlData.controlMode << "\n" <<
				rpcCmdData.getFullDescription(CTRL_PID_RESET_ENABLED) << ": " << taskData->controlData.pidResetEnabled << "\n" <<
		        rpcCmdData.getFullDescription(CTRL_LIFESPAN) << ": " << taskData->controlData.lifespan << "\n" <<
		        "\n" <<
		        "--- RAMP TASK DATA ---" << "\n" <<
		        rpcCmdData.getFullDescription(RAMP_SLOPE) << ": " << taskData->rampData.slope << "\n" <<
		        rpcCmdData.getFullDescription(RAMP_INTERCEPT) << ": " << taskData->rampData.intercept << "\n" <<
		        rpcCmdData.getFullDescription(RAMP_LIFESPAN) << ": " << taskData->rampData.lifespan << "\n" <<
		        rpcCmdData.getFullDescription(RAMP_LIFESPAN_AFTER_STAB) << ": " << taskData->rampData.lifespanAfterStabilization << "\n" <<
		        "\n" <<
		        "--- APPROACH TASK DATA ---" << "\n" <<
		        rpcCmdData.getFullDescription(APPR_JOINTS_VELOCITIES) << ": " << taskData->getValueDescription(APPR_JOINTS_VELOCITIES) << "\n" <<
		        rpcCmdData.getFullDescription(APPR_JOINTS_PWM_LIMITS) << ": " << taskData->getValueDescription(APPR_JOINTS_PWM_LIMITS) << "\n" <<
				rpcCmdData.getFullDescription(APPR_JOINTS_PWM_LIMITS_ENABLED) << ": " << taskData->approachData.jointsPwmLimitsEnabled << "\n" <<
		        rpcCmdData.getFullDescription(APPR_LIFESPAN) << ": " << taskData->approachData.lifespan << "\n" <<

				"";
		break;

	case TASKS:
		cout << "\n" <<
				"\n" << 
				"------- TASK LIST -------" << "\n" <<
					"\n";

		for (size_t i = 0; i < taskList.size(); i++){
			
			cout << "- ";
			switch (taskList[i]->getTaskName()){

			case STEP:
				cout << "STEP\t" << (dynamic_cast<StepTask*>(taskList[i]))->getConstantPwmDescription() << "\n";
				break;
			case CONTROL:
				cout << "CONTROL\t" << (dynamic_cast<ControlTask*>(taskList[i]))->getPressureTargetValueDescription() << "\n";
				break;
			case APPROACH_AND_CONTROL:
				cout << "APPROACH & CONTROL\t" << (dynamic_cast<ControlTask*>(taskList[i]))->getPressureTargetValueDescription() << "\n";
				break;
			case APPROACH:
				cout << "APPROACH\t" << "\n";
				break;
			case RAMP:
				cout << "RAMP\t" << (dynamic_cast<RampTask*>(taskList[i]))->getPressureTargetValueDescription() << "\n";
				break;

			}
		}
	}
}

void TaskThread::help(RPCCommandsData &rpcCmdData){

	cout << "\n" <<
		    "\n" <<
            "----------- HELP -----------" << "\n" <<
		    "---- AVAILABLE COMMANDS ----" << "\n" <<
		    "\n" <<
		    rpcCmdData.getFullDescription(HELP) << "\n" <<
		    rpcCmdData.getFullDescription(SET) << "\n" <<
		    rpcCmdData.getFullDescription(TASK) << "\n" <<
		    rpcCmdData.getFullDescription(VIEW) << "\n" <<
		    rpcCmdData.getFullDescription(START) << "\n" <<
		    rpcCmdData.getFullDescription(STOP) << "\n" <<
		    rpcCmdData.getFullDescription(OPEN) << "\n" <<
		    rpcCmdData.getFullDescription(ARM) << "\n" <<
		    rpcCmdData.getFullDescription(QUIT) << "\n";
	
}			
