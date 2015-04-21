#ifndef __ICUB_PLANTIDENTIFICATION_CONTROLTASK_H__
#define __ICUB_PLANTIDENTIFICATION_CONTROLTASK_H__

#include "iCub/plantIdentification/task/Task.h"
#include "iCub/plantIdentification/data/TaskData.h"
#include "iCub/plantIdentification/util/ControllersUtil.h"
#include "iCub/plantIdentification/util/PortsUtil.h"

#include <iCub/ctrl/pids.h>
#include <yarp/os/Bottle.h>
#include <yarp/os/Value.h>

namespace iCub {
    namespace plantIdentification {

        class ControlTask : public Task {

            private:

				iCub::plantIdentification::ControlTaskData *controlData;
				std::vector<iCub::ctrl::parallelPID*> pid;
				// pid options bottle when error >= 0
				std::vector<yarp::os::Bottle> pidOptionsPE;
				// pid options bottle when error < 0
				std::vector<yarp::os::Bottle> pidOptionsNE;
				std::vector<double> pressureTargetValue;
				
				/* variables used for error integral reset mode */
				bool resetErrOnContact;
				std::vector<bool> fingerIsInContact;

				// TODO to be removed
				std::vector<double> currentKp;
				std::vector<double> kpPe;
				std::vector<double> kpNe;
				std::vector<double> previousError;

            public:

                ControlTask(iCub::plantIdentification::ControllersUtil *controllersUtil,iCub::plantIdentification::PortsUtil *portsUtil,iCub::plantIdentification::TaskCommonData *commonData,iCub::plantIdentification::ControlTaskData *controlData,double pressureTargetValue,bool resetErrOnContact = false);

				std::string getPressureTargetValueDescription();

				virtual void init();

				virtual void buildLogData(LogData &logData);

				virtual void calculatePwm();

				virtual void release();

			private :

				void addOption(yarp::os::Bottle &bottle,char *paramName,yarp::os::Value paramValue);

				void addOption(yarp::os::Bottle &bottle,char *paramName,yarp::os::Value paramValue1,yarp::os::Value paramValue2);

				double calculateTt(iCub::plantIdentification::ControlTaskOpMode gainsSet,int index);

        };
    } //namespace plantIdentification
} //namespace iCub

#endif
