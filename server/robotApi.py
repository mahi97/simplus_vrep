try:
    import vrep
except:
    print('--------------------------------------------------------------')
    print('"vrep.py" could not be imported. This means very probably that')
    print('either "vrep.py" or the remoteApi library could not be found.')
    print('Make sure both are in the same folder as this file,')
    print('or appropriately adjust the file "vrep.py"')
    print('--------------------------------------------------------------')
    print('')

import time
import numpy as np
from matplotlib import pyplot as plt
import math


class VrepApi:
    def __init__(self, server_ip='127.0.0.1', server_port=19999, waitUntilConnected=True,
                 doNotReconnectOnceDisconnected=True, timeOutInMs=5000, commThreadCycleInMs=5):
        vrep.simxFinish(-1)  # just in case, close all opened connections
        self.clientID = vrep.simxStart(server_ip, server_port, waitUntilConnected, doNotReconnectOnceDisconnected,
                                       timeOutInMs, commThreadCycleInMs)  # Connect to V-REP
        print("client id", self.clientID)
        self.robot_api = None
        self.server_api = None

    def init_robotApi(self, trapConfig=None, robot_base='ePuck_base', robot_namespace="ePuck_",
                      robot_motors={"left": 'leftJoint', "right": 'rightJoint', "radius": 0.02},
                      proximity_sensor={"num": 8, "name": 'proxSensor'}, camera={"name": 'camera', "joint": None},
                      color_sensor={"num": 1, "name": 'lightSensor'}, gps_enabled=True):
        return robotApi(remoteApi=self.clientID, trapConfig=trapConfig, robot_base=robot_base,
                        robot_namespace=robot_namespace, robot_motors=robot_motors, proximity_sensor=proximity_sensor,
                        camera=camera, color_sensor=color_sensor, gps_enabled=gps_enabled)

    def init_serverApi(self,
                       serverConfig=r'serverconfig.txt'):
        return serverApi(remoteApi=self.clientID, serverConfig=serverConfig)


class actionClass:
    def __init__(self, remoteApi, action, max_range=1.0, success_score=1.0, failure_score=-0.5, obejcts_names=[]):
        self.action = action
        self.clientID = remoteApi
        self.range = float(max_range)
        self.success_score = float(success_score)
        self.failure_score = float(failure_score)
        self.obejcts_names = obejcts_names
        self.objects_distances = []
        for i in self.obejcts_names:
            temp1, oh = vrep.simxGetObjectHandle(self.clientID, i, vrep.simx_opmode_blocking)
            response = vrep.simxGetObjectPosition(self.clientID, oh, -1, vrep.simx_opmode_blocking)
            self.objects_distances.append([response[1][0], response[1][1], response[1][2]])

    def applyAction(self, x, y, z):
        target_distances = []
        for i in range(0, len(self.objects_distances)):
            s = pow(self.objects_distances[i][0] - x, 2) + pow(self.objects_distances[i][1] - y, 2) + pow(
                self.objects_distances[i][2] - z, 2)
            target_distances.append(pow(s, 0.5))
        index_min = np.argmin(np.array(target_distances))
        if target_distances[index_min] <= self.range:
            self.logAction(x, y, z, index_min, target_distances[index_min], self.success_score)
            return self.success_score
        else:
            self.logAction(x, y, z, index_min, target_distances[index_min], self.failure_score)
            return self.failure_score

    def logAction(self, x, y, z, index_min, distance, score):
        print(self.action)
        print(x, y, z)
        print(self.obejcts_names[index_min], self.objects_distances[index_min])
        print(distance, score)


class trapClass:
    def __init__(self, remoteApi, trap, max_range=1.0, penalty=1.0, bandgap_range=0.5, obejcts_names=[]):
        self.trap_activated = False
        self.trap = trap
        self.clientID = remoteApi
        self.range = float(max_range)
        self.penalty = float(penalty)
        self.bandgap_range = float(bandgap_range)
        self.obejcts_names = obejcts_names
        self.objects_distances = []
        for i in self.obejcts_names:
            temp1, oh = vrep.simxGetObjectHandle(self.clientID, i, vrep.simx_opmode_blocking)
            response = vrep.simxGetObjectPosition(self.clientID, oh, -1, vrep.simx_opmode_blocking)
            self.objects_distances.append([response[1][0], response[1][1], response[1][2]])

    def checkTrap(self, x, y, z):
        if (self.trap_activated == False):
            target_distances = []
            for i in range(0, len(self.objects_distances)):
                s = pow(self.objects_distances[i][0] - x, 2) + pow(self.objects_distances[i][1] - y, 2) + pow(
                    self.objects_distances[i][2] - z, 2)
                target_distances.append(pow(s, 0.5))
            index_min = np.argmin(np.array(target_distances))
            if target_distances[index_min] <= self.range:
                self.logTrap(x, y, z, index_min, target_distances[index_min])
                self.trap_activated = True
                return self.penalty
            else:
                return 0
        else:
            target_distances = []
            for i in range(0, len(self.objects_distances)):
                s = pow(self.objects_distances[i][0] - x, 2) + pow(self.objects_distances[i][1] - y, 2) + pow(
                    self.objects_distances[i][2] - z, 2)
                target_distances.append(pow(s, 0.5))
            index_min = np.argmin(np.array(target_distances))
            if target_distances[index_min] >= self.range + self.bandgap_range:
                self.logTrap(x, y, z, index_min, target_distances[index_min])
                self.trap_activated = False
            return 0

    def logTrap(self, x, y, z, index_min, distance):
        print(self.trap)
        print(x, y, z)
        print(self.obejcts_names[index_min], self.objects_distances[index_min])
        print(distance)


class robotApi:

    # constructor for client api class
    # arg nodeName : type string : name of client for connecting to api
    # arg channelName : type string : name of channel used by api
    # arg robot_base : type string : name of robot model in V-rep
    # arg robot_namespace : type string : prefix string for all sensors and joints 
    # arg robot_motors : type dictionary : {"left": name of left wheel joint , "right" : name of right wheel joint , "radius": radius of wheel model in V-rep}
    # arg proximity_sensor : type dictionary : {"num": number of proximity sensors ,"name":prefix of proximity sensor's name}
    # arg camera : type dictionary : {"name": prefix of Visionsensor's name ,"joint": name of joint for camera rotation, set to None if no joint exists}
    # color_sensor : type dictionary : {"num": number of color sensors ,"name":prefix of color sensor's name}
    def __init__(self, remoteApi, trapConfig=None, robot_base='ePuck', robot_namespace="ePuck_",
                 robot_motors={"left": 'leftJoint', "right": 'rightJoint', "radius": 0.02},
                 proximity_sensor={"num": 8, "name": 'proxSensor'}, camera={"name": 'camera', "joint": None},
                 color_sensor={"num": 1, "name": 'lightSensor'}, gps_enabled=True):
        self.gps_enabled = gps_enabled
        self.clientID = remoteApi
        temp1, self.left = vrep.simxGetObjectHandle(self.clientID, robot_namespace + robot_motors["left"],
                                                    vrep.simx_opmode_blocking)
        temp2, self.right = vrep.simxGetObjectHandle(self.clientID, robot_namespace + robot_motors["right"],
                                                     vrep.simx_opmode_blocking)
        self.wheel_radius = robot_motors["radius"]
        temp3, self.robot_base = vrep.simxGetObjectHandle(self.clientID, robot_base, vrep.simx_opmode_blocking)
        self.robot_width = self.__getRobotWidth__()
        temp4, self.camera = vrep.simxGetObjectHandle(self.clientID, robot_namespace + camera["name"],
                                                      vrep.simx_opmode_blocking)
        if (camera["joint"]):
            temp, self.camera_joint = vrep.simxGetObjectHandle(self.clientID, robot_namespace + camera["joint"],
                                                               vrep.simx_opmode_blocking)
        else:
            self.camera_joint = None

        self.proxSensors = []
        for i in range(1, proximity_sensor["num"] + 1):
            temp, sensor = vrep.simxGetObjectHandle(self.clientID, robot_namespace + proximity_sensor["name"] + str(i),
                                                    vrep.simx_opmode_blocking)
            self.proxSensors.append(sensor)

        self.colorSensors = []
        # for i in range(1,color_sensor["num"]+1):
        #     if(i==0):i=''
        #     temp,sensor=vrep.simxGetObjectHandle(self.clientID,robot_namespace+color_sensor["name"]+str(i),vrep.simx_opmode_blocking)
        #     self.colorSensors.append(sensor)
        for i in ['', '_l', '_r']:
            temp, sensor = vrep.simxGetObjectHandle(self.clientID, robot_namespace + color_sensor["name"] + str(i),
                                                    vrep.simx_opmode_blocking)
            self.colorSensors.append(sensor)

        self.traps_dict = None
        if (trapConfig != None):
            self.traps_dict = {}
            self.parseConfig(trapConfig)

    def __getRobotWidth__(self):
        response_right = vrep.simxGetObjectPosition(self.clientID, self.right, self.robot_base,
                                                    vrep.simx_opmode_blocking)
        response_left = vrep.simxGetObjectPosition(self.clientID, self.left, self.robot_base, vrep.simx_opmode_blocking)
        right_x, right_y = response_right[1][0:2]
        left_x, left_y = response_left[1][0:2]
        x_width = abs((left_x) - (right_x))
        y_width = abs((left_y) - (right_y))
        # print("xxxx",right_x,left_x)
        # print("yyy",right_y,left_y)
        return max(x_width, y_width)

    def __getRobotXYZ__(self):
        returnCode_pose, position = vrep.simxGetObjectPosition(self.clientID, self.robot_base, -1,
                                                               vrep.simx_opmode_blocking)
        return position

    def checkAllTraps(self):
        penalty = 0
        pose = self.__getRobotXYZ__()

        for t in self.traps_dict.keys():
            penalty += self.traps_dict.get(t).checkTrap(pose)

        return penalty

    def setLED(self, color):

        if (color == "red"):
            returnCode, outInts, outFloats, outStrings, outBuffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                                'Simplus_monitor',
                                                                                                vrep.sim_scripttype_childscript,
                                                                                                'remote_led_change',
                                                                                                [21002], [], [],
                                                                                                bytearray(),
                                                                                                vrep.simx_opmode_blocking)
            if (returnCode == 0):
                return 'red'
            else:
                return -1
        if (color == "green"):
            returnCode, outInts, outFloats, outStrings, outBuffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                                'Simplus_monitor',
                                                                                                vrep.sim_scripttype_childscript,
                                                                                                'remote_led_change',
                                                                                                [21003], [], [],
                                                                                                bytearray(),
                                                                                                vrep.simx_opmode_blocking)
            if (returnCode == 0):
                return 'green'
            else:
                return -1
        if (color == "blue"):
            returnCode, outInts, outFloats, outStrings, outBuffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                                'Simplus_monitor',
                                                                                                vrep.sim_scripttype_childscript,
                                                                                                'remote_led_change',
                                                                                                [21004], [], [],
                                                                                                bytearray(),
                                                                                                vrep.simx_opmode_blocking)
            if (returnCode == 0):
                return 'blue'
            else:
                return -1
        else:
            returnCode, outInts, outFloats, outStrings, outBuffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                                'Simplus_monitor',
                                                                                                vrep.sim_scripttype_childscript,
                                                                                                'remote_led_change',
                                                                                                [21001], [], [],
                                                                                                bytearray(),
                                                                                                vrep.simx_opmode_blocking)
            if (returnCode == 0):
                return ''
            else:
                return -1

    # function to get Image 
    # arg : None
    # return : -1 : if the api fails 
    # return : 3D Numpy array holding RGB values 
    def getCameraImage(self):
        returnCode, image_resolution, image_array = vrep.simxGetVisionSensorImage(self.clientID, self.camera, 0,
                                                                                  vrep.simx_opmode_blocking)
        if (returnCode == 0):
            return [image_array, image_resolution[0], image_resolution[1]]
            # image_array=(np.frombuffer(response[2], dtype=np.uint8))
            # return np.flip(np.reshape(image_array,[response[1][0],response[1][1],3]),0)
        else:
            return -1

    # function to get color sensor output
    # arg : sensor_index : integer : index of color sensor : 0<= index  < number of color sensors 
    # return : -1 : if the api fails 
    # return : 3D Numpy array holding RGB values
    def getColorSensor(self, sensor_index=0):
        if (sensor_index >= len(self.colorSensors)): return -1
        returnCode, image_resolution, image_array = vrep.simxGetVisionSensorImage(self.clientID,
                                                                                  self.colorSensors[sensor_index], 0,
                                                                                  vrep.simx_opmode_blocking)
        if (returnCode == 0):
            image_array = (np.array(image_array, dtype=np.uint8))
            return image_array[24:27]
            # image_array=(np.frombuffer(response[2], dtype=np.uint8))
            # return np.flip(np.reshape(image_array,[response[1][0],response[1][1],3]),0)
        else:
            return -1

    # function to get proximity sensor output
    # arg : sensor_index : integer : index of color sensor : 0<= index  < number of proximity sensors 
    # return : -1 : if the api fails 
    # return : [0,0] if no obstacle is detected 
    # return : [1, d] if obstacle is detected : d is distance from sensor to obstacle
    def getProximitySensor(self, sensor_index=0):
        returnCode, detectionState, detectedPoint, detectedObjectHandle, detectedSurfaceNormalVector = vrep.simxReadProximitySensor(
            self.clientID, self.proxSensors[sensor_index], vrep.simx_opmode_blocking)
        # print("proximity",returnCode,detectionState)
        if (returnCode == 0):
            if (detectionState == True):
                return [True, pow(pow(detectedPoint[0], 2) + pow(detectedPoint[1], 2) + pow(detectedPoint[2], 2), 0.5)]
            else:
                return [False, 0]
        else:
            return -1

    # function to get proximity sensor output
    # arg : none
    # return : -1 : if the api fails 
    # return : [x,y,z,roll,pitch,yaw] if gps is enabled
    # return : [0,0,0,roll,pitch,yaw] if gps is disabled
    def getRobotPose(self):
        returnCode_pose, position = vrep.simxGetObjectPosition(self.clientID, self.robot_base, -1,
                                                               vrep.simx_opmode_blocking)
        returnCode_orient, eulerAngles = vrep.simxGetObjectOrientation(self.clientID, self.robot_base, -1,
                                                                       vrep.simx_opmode_blocking)

        if (returnCode_pose == 0 and returnCode_orient == 0):
            angles_in_degree = [(i + math.pi / 2) * 180 / math.pi for i in eulerAngles]

            if (self.gps_enabled):
                return [position[0], position[1], position[2], angles_in_degree[0], angles_in_degree[1],
                        angles_in_degree[2]]
            else:
                return [0, 0, 0, angles_in_degree[0], angles_in_degree[1], angles_in_degree[2]]

    # function to set robot speed
    # arg : linear : integer : desired linear speed
    # arg : angular : integer : desired angular speed
    # return : none
    def setRobotSpeed(self, linear=0.0, angular=0.0):
        right_rotation = (linear + angular * self.robot_width / 2) / self.wheel_radius
        left_rotation = (linear - angular * self.robot_width / 2) / self.wheel_radius
        vrep.simxPauseCommunication(self.clientID, True)
        vrep.simxSetJointTargetVelocity(self.clientID, self.right, right_rotation, vrep.simx_opmode_oneshot)
        vrep.simxSetJointTargetVelocity(self.clientID, self.left, left_rotation, vrep.simx_opmode_oneshot)
        vrep.simxPauseCommunication(self.clientID, False)

    def parseConfig(self, config_file):
        with open(config_file, 'r') as fp:
            for line in fp:
                ls = line.split(';')
                ob = ls[1].split(',')
                ix = ls[2].split(',')
                ob_indexed = []
                for i in range(0, len(ob)):
                    temp = [ob[i]]
                    if (int(ix[i]) > 1):
                        for j in range(0, int(ix[i]) - 1):
                            temp.append(ob[i] + str(j))
                    ob_indexed.extend(temp)
                tc = trapClass(remoteApi=self.clientID, trap=ls[0], max_range=ls[3], bandgap_range=ls[4], penalty=ls[5],
                               obejcts_names=ob_indexed)
                self.traps_dict.update({ls[0]: tc})


class serverApi:

    # constructor for server api class
    # arg nodeName : type string : name of server for connecting to api
    # arg channelName : type string : name of channel used by api
    def __init__(self, remoteApi, serverConfig=None):
        self.clientID = remoteApi
        self.actions_dict = None
        if (serverConfig != None):
            self.actions_dict = {}
            self.parseConfig(serverConfig)

    def parseConfig(self, config_file):
        with open(config_file, 'r') as fp:
            for line in fp:
                ls = line.split(';')
                ob = ls[1].split(',')
                ix = ls[2].split(',')
                ob_indexed = []
                for i in range(0, len(ob)):
                    temp = [ob[i]]
                    if (int(ix[i]) > 1):
                        for j in range(0, int(ix[i]) - 1):
                            temp.append(ob[i] + str(j))
                    ob_indexed.extend(temp)
                ac = actionClass(remoteApi=self.clientID, action=ls[0], max_range=ls[3], success_score=ls[4],
                                 failure_score=ls[5], obejcts_names=ob_indexed)
                self.actions_dict.update({ls[0]: ac})

    def callAction(self, action, x, y, z):
        if (action in self.actions_dict.keys()):
            return self.actions_dict.get(action).applyAction(x, y, z)
        else:
            return 0

    def set_score(self, team_id, team_score):
        return_code, o_int, o_float, o_string, o_buffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                      'Game_manager',
                                                                                      vrep.sim_scripttype_childscript,
                                                                                      'remote_set_score',
                                                                                      [team_id], [], [team_score],
                                                                                      bytearray(),
                                                                                      vrep.simx_opmode_blocking)
        return return_code

    def set_name(self, team_name):
        return_code, o_int, o_float, o_string, o_buffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                      'Game_manager',
                                                                                      vrep.sim_scripttype_childscript,
                                                                                      'remote_get_name',
                                                                                      [], [], [team_name],
                                                                                      bytearray(),
                                                                                      vrep.simx_opmode_blocking)
        return o_int[0]

    def get_status(self):
        return_code, o_int, o_float, o_string, o_buffer = vrep.simxCallScriptFunction(self.clientID,
                                                                                      'Game_manager',
                                                                                      vrep.sim_scripttype_childscript,
                                                                                      'remote_get_sim_status',
                                                                                      [], [], [],
                                                                                      bytearray(),
                                                                                      vrep.simx_opmode_blocking)
        return o_int[0]

    # function to get server time in ms
    # arg : None
    # return : -1 : if the api fails 
    # return : integer : server time in milliseconds
    def getServerTime(self):
        response = vrep.simxGetServerTimeInMs(vrep.simx_opmode_blocking)
        if (response[0]):
            return response[1]
        else:
            return -1

    # function to get server state
    # arg : None
    # return : -1 : if the api fails 
    # return : string : "paused" 
    # return : string : "stopped"
    # return : string : "running"
    def getServerState(self):
        response = vrep.simxGetSimulationState(vrep.simx_opmode_blocking)
        if (response[0]):
            if (response[1] == 0):
                return "stopped"
            elif (response[1] == 8):
                return "paused"
            else:
                return "running"
        else:
            return -1

    # function to stop simulation
    # arg : None
    # return : -1 : if stoping the simulation fails
    # return : integer  : at least 0 if simulation is succesfully stopped
    def stopSimulation(self):
        response = vrep.simxStopSimulation(self.clientID, operationMode=vrep.simx_opmode_blocking)
        if (response == 0):
            print(response)
        else:
            return -1

    # function to start simulation
    # arg : None
    # return : -1 : if starting the simulation fails
    # return : integer  : at least 0 if simulation is succesfully started
    def startSimulation(self):
        response = vrep.simxStartSimulation(self.clientID, operationMode=vrep.simx_opmode_blocking)
        if (response):
            print("starign simulation")

            print(response)
        else:
            print("starign failed")
            return -1

    # function to pause simulation
    # arg : None
    # return : -1 : if pausing the simulation fails
    # return : integer  : at least 0 if simulation is succesfully paused
    def pauseSimulation(self):
        response = vrep.simxPauseSimulation(self.clientID, vrep.simx_opmode_blocking)
        if (response):
            print(response)
        else:
            return -1


def show_image(inputimage):
    image_array = (np.array(inputimage[0], dtype=np.uint8))
    im = np.flip(np.reshape(image_array, [inputimage[1], inputimage[2], 3]), 0)
    print(im)
    plt.imshow(im)
    plt.show()


def main():
    vapi = VrepApi()
    sa = vapi.init_serverApi()
    sa.startSimulation()
    print("step1")
    time.sleep(0.1)
    ra = vapi.init_robotApi()
    time.sleep(0.1)

    print(ra.getColorSensor(1))
    # print("getting robot pose",ra.getRobotPose())
    counter = 0
    col = ['red', 'green', 'blue', 'akldjf']
    obstacle = 0
    while True:
        obstacle = 0
        col0 = np.array(ra.getColorSensor(0))
        col1 = np.array(ra.getColorSensor(1))
        col2 = np.array(ra.getColorSensor(2))
        col_total = (col1 + col0 + col2)
        print(ra.setLED(col[np.argmax(col_total)]))
        for i in range(2, 6):
            obstacle += ra.getProximitySensor(i)[0]
        if (obstacle == 0):
            ra.setRobotSpeed(0.05, 0.0)
        else:
            ra.setRobotSpeed(0.00, 0.5)
        time.sleep(0.25)
        counter += 1
        if (counter > 1000): break
    sa.stopSimulation()
    vrep.simxFinish(vapi.clientID)
    time.sleep(25)


if __name__ == '__main__':
    main()