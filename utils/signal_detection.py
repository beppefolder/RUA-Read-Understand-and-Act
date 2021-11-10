# -*- coding: utf-8 -*-

import numpy as np
import cv2
import os

class Detection_Helper():

    def __init__(self, reference_template, window_size=16):
        self.WINDOW_SIZE = window_size
        self.template = reference_template

    def compute_sift_imgs(self, img1, img2):

        #sift = cv2.xfeatures2d.SIFT_create()
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)
        return kp1, kp2, des1, des2

    def sift_ratio(self, matches):
        good = []
        good_m = []

        for m, n in matches:
            if m.distance < 0.72 * n.distance:
                good.append([m])
                good_m.append(m)
        return good, good_m

    def find_centre_coords(self, coords):
        x = []
        y = []
        for c in coords:
            x.append(c[0])
            y.append(c[1])

        x_median = np.median(x)
        y_median = np.median(y)

        return x_median, y_median

    def look_for_signal(self, rgb_image):

        print("Computing SIFT on the image.. ")
        kp1, kp2, des1, des2 = self.compute_sift_imgs(self.template, rgb_image)
        # BFMatcher with default params
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)

        # Apply ratio test
        good, good_m = self.sift_ratio(matches)

        if len(good) < 10:
            return False, None, None
        else:
            coords = [kp2[good_m[i].trainIdx].pt for i in range(len(good))]
            x_c, y_c = self.find_centre_coords(coords)
            return True, x_c, y_c

    def inpaint_d_img(self, d_img):
        d_img = d_img.astype('float32')
        mask = np.where(d_img == 0, 255, 0).astype('uint8')
        d_img = cv2.inpaint(d_img, mask, 3, cv2.INPAINT_TELEA)
        d_img = cv2.medianBlur(d_img, 3)
        d_img = d_img[1:-1, 1:-1]
        d_img = cv2.copyMakeBorder(d_img, 1, 1, 1, 1, cv2.BORDER_REFLECT)
        return d_img


    def compute_depth_distance(self, x_c, y_c, depth):
        HALF_WINDOW_SIZE = int(self.WINDOW_SIZE / 2)

        # INPAINTING
        # define masks. Points where depth is = 0.
        depth = self.inpaint_d_img(depth)
        
        bottom_limit = y_c - HALF_WINDOW_SIZE
        upper_limit = y_c + HALF_WINDOW_SIZE
        left_limit = x_c - HALF_WINDOW_SIZE
        right_limit = x_c + HALF_WINDOW_SIZE
        final_depth = depth[bottom_limit:upper_limit, left_limit:right_limit]

        depth_value = np.median(final_depth)

        return depth_value