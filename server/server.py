from __future__ import print_function
import logging

import grpc

import simplus_pb2
import simplus_pb2_grpc
from robotApi import *
import time
import array


def run():

    vapi = VrepApi()
    sa = vapi.init_serverApi()
    is_started = False
    while not is_started:
        is_started = sa.get_status()
    # sa.startSimulation()
    print("step1")
    time.sleep(0.1)
    with grpc.insecure_channel(
            target='localhost:50051',
            options=[('grpc.lb_policy_name', 'pick_first'),
                     ('grpc.enable_retries', 0), ('grpc.keepalive_timeout_ms',
                                                  10000)]) as channel:
        stub = simplus_pb2_grpc.SimPlusStub(channel)
        # Timeout in seconds.
        response = stub.Start(simplus_pb2.WorldInfo(team_size=2,
                                                    robot_per_team=2,
                                                    color_sensor_size=2,
                                                    proximity_sensor_size=3,
                                                    check_points=
                                                    [simplus_pb2.CheckPoint(color='red', point=10),
                                                     simplus_pb2.CheckPoint(color='green', point=5)]), timeout=1)
        print("Client Received: " + response.name)
        my_team_id = 0
        my_team_id = max(sa.set_name(response.name), my_team_id)
        ra = vapi.init_robotApi()
        team_score = 0
        team_name = response.name
        for i in range(100):
            is_started = sa.get_status()
            while not is_started:
                is_started = sa.get_status()
            a = time.process_time()

            image = ra.getCameraImage()
            image_array = np.array(image[0], dtype=np.uint8)

            colors = [ra.getColorSensor(i) for i in range(3)]
            proxim = [ra.getProximitySensor(i) for i in range(8)]
            pos = ra.getRobotPose()
            response = stub.Action(
                simplus_pb2.Observations(
                    server=simplus_pb2.ServerInfo(time=i, server_state='running', my_score=0, opp_score=1),
                    robots=[simplus_pb2.Observation(
                        camera=simplus_pb2.Image(w=image[1], h=image[2], raw=array.array('B', image_array).tobytes()),
                        colors=[simplus_pb2.Pixel(r=colors[i][0], g=colors[i][1], b=colors[i][2]) for i in range(3)],
                        distances=[simplus_pb2.Proximity(detected=proxim[i][0], distance=proxim[i][1]) for i in range(8)],
                        pos=simplus_pb2.Position(x=pos[0], y=pos[1], z=pos[2], roll=pos[3], pitch=pos[4], yaw=pos[5],
                                                 gps_enabled=ra.gps_enabled)
                    ) for i in range(1)]
                )
            )
            print(1.0 / (time.process_time() - a))
            for res in response.commands:
                print('Robot ' + str(res.id) + ' Command: ' + str(res.linear) + ' ' + str(res.angular) + ' LED: ' +
                      res.LED)
                ra.setRobotSpeed(linear=res.linear, angular=res.angular)
                ra.setLED(color=res.LED)
                for action in res.actions:
                    team_score += sa.callAction(action.type, action.x, action.y, action.z)
            # team_score -= ra.checkAllTraps()
            sa.set_score(my_team_id, str(i))

            print(1.0 / (time.process_time() - a))

        response = stub.End(
            simplus_pb2.Ending(server=simplus_pb2.ServerInfo(time=i, server_state='running', my_score=0, opp_score=1)))
        print('END IS: ' + response.message)


if __name__ == '__main__':
    logging.basicConfig()
    run()