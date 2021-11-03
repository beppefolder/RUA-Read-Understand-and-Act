# -*- coding: utf-8 -*-

import os
import cv2
from pyrobot import Robot
import pyrobot.utils.util as prutil
import numpy as np
from utils.robot_movements import Robot_Movements_Helper
from utils.signal_detection import Detection_Helper

def compute_3d_point(bot, poi):
    """
        Input:
            -poi : Stands for "point of interest". It is a list [x_c, y_c]
    """
    x_c, y_c = poi[0], poi[1]
    camera = bot.camera
    trans, rot, T = camera.get_link_transform(camera.cam_cf, camera.base_f)
    base2cam_trans = np.array(trans).reshape(-1, 1)
    base2cam_rot = np.array(rot)
    pts_in_cam = prutil.pix_to_3dpt(d_img, [y_c], [x_c], camera.get_intrinsics(), 1.0) 
    pts = pts_in_cam[:3, :].T
    pts = np.dot(pts, base2cam_rot.T)
    pts = pts + base2cam_trans.T
    return pts


def reach_signal(bot_moves, helper_detection, poi, rgb_img, d_img):
    x_c, y_c = poi[0], poi[1]
    depth = helper_detection.compute_depth_distance(x_c, y_c, d_img)

    THRESHOLD_DISTANCE = 2.0
    DISTANCE_LIMIT = 0.2
    INTERMEDIATE_STEP = 1.0


    while depth > THRESHOLD_DISTANCE:
        pts = compute_3d_point(bot_moves.robot, [x_c, y_c])
        print("3D point as [x, y, z]: " , pts)
        thetha = np.arctan2(y_c, x_c)
        target_position = [INTERMEDIATE_STEP, 0.0, 0.0]
        
        bot_moves.turn(thetha)
        bot_moves.reach_relative_point(target_position)

        print('Acquisition of the frame RGBD after intermediate step...')
        rgb_img, d_img = bot_moves.read_frame()

        found, x_c, y_c = helper_detection.look_for_signal(rgb_img)
        if not found:
            return False
        depth = helper_detection.compute_depth_distance(x_c, y_c, d_img)
    

    pts = compute_3d_point(bot_moves.robot, [x_c, y_c])
    print("3D point as [x, y, z]: " , pts)
    thetha = np.arctan2(y_c, x_c)
    distance = np.sqrt(x_c**2 + y_c**2) # compute distance on diagonal
    target_position = [distance - DISTANCE_LIMIT, 0.0, 0.0] #stop at limit
    
    bot_moves.turn(thetha)
    bot_moves.reach_relative_point(target_position)
    return True
            

if __name__ == '__main__':
    bot = Robot('locobot')
    bot.camera.reset()

    bot_moves = Robot_Movements_Helper(bot)
    template = cv2.imread("utils/template.jpg")
    helper_detection = Detection_Helper(template)
    
    #Keep moving until signal is not found. Each time performs
    ANGLES_RADIANT = np.pi/3
    MAX_ROTATIONS = 6

    found, x_c, y_c = False, None, None
    for i in range(MAX_ROTATIONS):
        print('{} Acquisition of the frame RGBD...'.format(i))
        rgb_img, d_img = bot_moves.read_frame()
        #rgb_img = cv2.cvtColor(cv2.imread('prova.png'), cv2.COLOR_BGR2RGB)
        #d_img = np.load('prova.npy')

        found, x_c, y_c = helper_detection.look_for_signal(rgb_img)
        if found:
            break
        else:
            bot_moves.left_turn(ANGLES_RADIANT)

    if found:
        #signal is found, so now we can manage the robot movement.
        print('Signal found...reaching it!')
        is_arrived = reach_signal(bot_moves, helper_detection, [x_c, y_c], rgb_img, d_img)
        
        if is_arrived:
            print('Robot arrived to destination...In front of the signal!')
        else:
            print('Something went wrong! Robot no longer sees the signal!')
    else:
        print('Stop signal NOT FOUND in the neighborhood... Hence, robot will not move!')