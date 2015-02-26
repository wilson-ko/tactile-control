#include "iCub/plantIdentification/task/StepTask.h"

#include "iCub/plantIdentification/plantIdentificationEnums.h"

using iCub::plantIdentification::StepTask;
using iCub::plantIdentification::LogData;
using iCub::plantIdentification::ControllersUtil;
using iCub::plantIdentification::PortsUtil;
using iCub::plantIdentification::TaskCommonData;
using iCub::plantIdentification::StepTaskData;

StepTask::StepTask(ControllersUtil *controllersUtil,PortsUtil *portsUtil,TaskCommonData *commonData,StepTaskData *stepData,double constantPwm):Task(controllersUtil,portsUtil,commonData,stepData->lifespan) {

	this->stepData = stepData;
	this->constantPwm = constantPwm;

	taskName = STEP;
	dbgTag = "StepTask: ";
}

void StepTask::calculatePwm(){

	pwmToUse = constantPwm;
}

void StepTask::buildLogData(LogData &logData){

	addCommonLogData(logData);

	logData.taskType = STEP;
	logData.taskOperationMode = 0;
	logData.targetValue = constantPwm;
}
