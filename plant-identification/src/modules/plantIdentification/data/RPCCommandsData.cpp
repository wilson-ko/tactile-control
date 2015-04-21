#include "iCub/plantIdentification/data/RPCCommandsData.h"

#include <iostream>
#include <sstream>
#include <string.h>
#include <stdlib.h>

using iCub::plantIdentification::RPCCommandsData;
using iCub::plantIdentification::RPCMainCmdName;
using iCub::plantIdentification::RPCSetCmdArgName;
using iCub::plantIdentification::RPCTaskCmdArgName;
using iCub::plantIdentification::RPCViewCmdArgName;
using iCub::plantIdentification::TaskName;

using std::string;
using std::pair;

RPCCommandsData::RPCCommandsData(){

	add("help",HELP,"THIS HELP");
	add("set",SET,"SET PARAMETERS (usage: 'set <paramName> <paramValue>')");
	add("task",TASK,"MANAGE TASKS (usage: 'task [pop | empty | add <taskType> <targetValue>]')");
	add("view",VIEW,"VIEW PARAMETERS/TASKS (usage: 'view [set | tasks]')");
	add("start",START,"START TASKS");
	add("stop",STOP,"STOP TASKS");
	add("open",OPEN,"STOP TASKS AND OPEN HAND");
	add("arm",ARM,"set ARM IN TASK POSITION");
	add("quit",QUIT,"QUIT MODULE");

	add("pwm_sign",PWM_SIGN,"PWM SIGN");
	add("pwm_sign",OBJ_DETECT_PRESS_THRESHOLDS,"OBJECT DETECTION PRESSURE THRESHOLDS");
	add("step_ls",STEP_LIFESPAN,"STEP TASK LIFESPAN");
	add("kp_pe",CTRL_PID_KPF,"CONTROL PID Kp (error >= 0)");
	add("ki_pe",CTRL_PID_KIF,"CONTROL PID Ki (error >= 0)");
	add("kp_ne",CTRL_PID_KPB,"CONTROL PID Kp (error < 0)");
	add("ki_ne",CTRL_PID_KIB,"CONTROL PID Ki (error < 0)");
	add("ctrl_op_mode",CTRL_OP_MODE,"CONTROL OPERATION MODE [0: err >= 0; 1: err < 0; 2: both]");
	add("ctrl_pid_reset",CTRL_PID_RESET_ENABLED,"PID RESET ENABLED [0: false; 1: true]");
	add("ctrl_ls",CTRL_LIFESPAN,"CONTROL TASK LIFESPAN");
	add("slope",RAMP_SLOPE,"RAMP SLOPE");
	add("intercept",RAMP_INTERCEPT,"RAMP INTERCEPT");
	add("ramp_ls",RAMP_LIFESPAN,"RAMP TASK LIFESPAN");
	add("ramp_ls_after_stab",RAMP_LIFESPAN_AFTER_STAB,"RAMP TASK LIFESPAN AFTER STABILIZATION");

	add("add",ADD,"add");
	add("empty",EMPTY,"empty");
	add("pop",POP,"pop");

	add("step",STEP,"STEP TASK");
	add("ctrl",CONTROL,"CONTROL TASK");
	add("appctrl",APPROACH_AND_CONTROL,"APPROACH & CONTROL TASK");
	add("ramp",RAMP,"RAMP TASK");

	add("set",SETTINGS,"SETTINGS");
	add("tasks",TASKS,"TASKS");

	dbgTag = "RPCCommandsData: ";
	
}

void RPCCommandsData::add(string rpcLabel,RPCMainCmdName enumLabel,string description){
	mainCmdMap.insert(std::pair<RPCMainCmdName,string>(enumLabel,rpcLabel));
	mainCmdDescMap.insert(std::pair<RPCMainCmdName,string>(enumLabel,description));
	mainCmdRevMap.insert(std::pair<string,RPCMainCmdName>(rpcLabel,enumLabel));
}

void RPCCommandsData::add(string rpcLabel,RPCSetCmdArgName enumLabel,string description){
	setCmdArgMap.insert(std::pair<RPCSetCmdArgName,string>(enumLabel,rpcLabel));
	setCmdArgDescMap.insert(std::pair<RPCSetCmdArgName,string>(enumLabel,description));
	setCmdArgRevMap.insert(std::pair<string,RPCSetCmdArgName>(rpcLabel,enumLabel));
}

void RPCCommandsData::add(string rpcLabel,RPCTaskCmdArgName enumLabel,string description){
	taskCmdArgMap.insert(pair<RPCTaskCmdArgName,string>(enumLabel,rpcLabel));
	taskCmdArgDescMap.insert(pair<RPCTaskCmdArgName,string>(enumLabel,description));
	taskCmdArgRevMap.insert(pair<string,RPCTaskCmdArgName>(rpcLabel,enumLabel));
}

void RPCCommandsData::add(string rpcLabel,RPCViewCmdArgName enumLabel,string description){
	viewCmdArgMap.insert(pair<RPCViewCmdArgName,string>(enumLabel,rpcLabel));
	viewCmdArgDescMap.insert(pair<RPCViewCmdArgName,string>(enumLabel,description));
	viewCmdArgRevMap.insert(pair<string,RPCViewCmdArgName>(rpcLabel,enumLabel));
}

void RPCCommandsData::add(string rpcLabel,TaskName enumLabel,string description){
	taskMap.insert(pair<TaskName,string>(enumLabel,rpcLabel));
	taskDescMap.insert(pair<TaskName,string>(enumLabel,description));
	taskRevMap.insert(pair<string,TaskName>(rpcLabel,enumLabel));
}

std::string RPCCommandsData::getFullDescription(RPCSetCmdArgName setCmdArgName){

	return setCmdArgDescMap[setCmdArgName] + " ('" + setCmdArgMap[setCmdArgName] + "')";
}

std::string RPCCommandsData::getFullDescription(RPCMainCmdName mainCmdName){

	return "'" + mainCmdMap[mainCmdName] + "' - " + mainCmdDescMap[mainCmdName];
}

void RPCCommandsData::setValues(std::string values,std::vector<double> &valueList){

	valueList.resize(0);
	
	char *valuesChar = new char[values.length() + 1];
	strcpy(valuesChar,values.c_str());
	char *target;
			
	target = strtok(valuesChar,"_");
	while(target != NULL){
		valueList.push_back(atof(target));
		target = strtok(NULL,"_");
	}
}

std::string RPCCommandsData::printValue(yarp::os::Value &value){

	std::stringstream valueString("");

	if (value.isDouble()) valueString << value.asDouble();
	else if (value.isInt()) valueString << value.asInt();
	else valueString << value.asString();

	return valueString.str();
}

