#!/usr/bin/env python

import numpy as np
import cv2
import math

_ROLLER_Y_MIN = 160
_ROLLER_Y_MAX = 340#herke
_ROLLER_X_MIN = 200
_ROLLER_X_MAX = 440
_R_INDEX = 2
_G_INDEX = 1
_B_INDEX = 0
_Y_COLOR_THRESH = 0.25

# _TEST_PATH = '/home/icub/tmp_massimo/tactile-control/gaussian-process-controller/'
_TEST_PATH = '/u/thermans/sandbox/icub_vision_test/test2/'

_HOUGH_THRESH = 50
_MASK_THRESH = 0.7
_BLACK_LINE_THRESH = 180
_END_SEARCH_EDGE_BUFFER = 20
_CLOSE_BW_IMG = False

_KULER_RED = (78./255, 18./255, 178./255)
_KULER_YELLOW = (25./255, 252./255, 1.)
_KULER_GREEN = (51./255., 178./255, 0.)
_KULER_BLUE = (204./255, 133./255, 20./255)
_KULER_RED1 = (0., 0., 1.)
_KULER_BLUE1 = (178./255, 113./255, 9./255)
_KULER_GREEN1 = (72./255, 255./255, 0.)

_MORPH_KERNEL = np.ones((3,3),np.uint8)
_MORPH_KERNEL[0,0] = 0
_MORPH_KERNEL[0,2] = 0
_MORPH_KERNEL[2,0] = 0
_MORPH_KERNEL[2,2] = 0


def test_on_imgs():
    for i in range(11,21):
        print _TEST_PATH+'test'+str(i)+'.tiff'
        img_i = cv2.imread(_TEST_PATH+'test'+str(i)+'.tiff')
        run_system(img_i)

def run_system(img_i):
    img_t = crop_img(img_i)
    blob_i, blob_mask = find_roller(img_t)
    line_info = find_lines(img_t, blob_mask)
    lines_i = line_info[0]
    cv2.imshow('img_i', img_i)
    cv2.imshow('img_t', img_t)
    cv2.imshow('roller', blob_i)
    cv2.imshow('lines', lines_i)
    cv2.waitKey()


def crop_img(img_in):
    # Ensure image is float 0 to 1
    if img_in.dtype == np.uint8:
        img_t = int_img2float(img_in)
    else:
        img_t = img_in[:]
    roll_img = img_t

    # Crop image
    img_t = img_t[_ROLLER_Y_MIN:_ROLLER_Y_MAX,
                  _ROLLER_X_MIN:_ROLLER_X_MAX,:]
    return img_t

def find_roller(img_t):
    # Herke -> select white pixels
    img_bw = cv2.cvtColor(img_t, cv2.COLOR_BGR2GRAY)
    mask_b = (img_bw > _MASK_THRESH).astype(np.uint8)

    mask_i = cv2.erode(mask_b, _MORPH_KERNEL,iterations = 2)
    mask_i = cv2.dilate(mask_i, _MORPH_KERNEL,iterations = 10)
    mask_i = cv2.erode(mask_i, _MORPH_KERNEL,iterations = 9)

    mask = mask_i.astype(np.bool)

    blob_img = np.zeros(img_t.shape, dtype=np.float32)
    blob_img[mask] = img_t[mask]

    return blob_img, mask

def find_lines(img_in, mask):
    img_bw = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)

    img_bw_u8 = (img_bw*255).astype(np.uint8)
    img_bw_u8[np.logical_not(mask)] = 255
    threshold = _BLACK_LINE_THRESH
    img_bw_u8[img_bw_u8 > threshold] = 255
    img_bw_u8[img_bw_u8 <= threshold] = 0
    lines = cv2.HoughLines(255 - img_bw_u8, 3, np.pi/90., _HOUGH_THRESH)

    disp_img = np.zeros(img_in.shape, np.float32)
    disp_img[mask] = img_in[mask]

    idx = 0
    first_found = False
    second_found = False
    first_line = []
    first_line_polar = []
    second_line = []
    second_line_polar = []
    theta_first = 0
    if lines is not None:
        print 'len(lines)',len(lines[0])
        for rho,theta in lines[0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 500*(-b))
            y1 = int(y0 + 500*(a))
            x2 = int(x0 - 500*(-b))
            y2 = int(y0 - 500*(a))
            g = 1 - idx * 0.04

            idx = idx + 1
            if not(first_found):
              first_found = True
              cv2.line(disp_img, (x1,y1), (x2,y2), _KULER_RED, 1)
              theta_first = theta
              first_line = [(x1,y1), (x2,y2)]
              first_line_polar = [rho, theta]
              continue
            dif = theta - theta_first
            if(dif > 0.5 * math.pi):
              dif = dif - math.pi
            if(dif < -0.5 * math.pi):
              dif = dif + math.pi
            if not(second_found) and abs(dif) > 0.25 * math.pi:
              second_found = True
              cv2.line(disp_img, (x1,y1), (x2,y2), _KULER_YELLOW, 1)
              second_line = [(x1,y1), (x2,y2)]
              second_line_polar = [rho, theta]
              continue

    if _CLOSE_BW_IMG:
        img_bw_u8 = cv2.dilate(img_bw_u8, _MORPH_KERNEL, iterations = 1)
        img_bw_u8 = cv2.erode(img_bw_u8, _MORPH_KERNEL, iterations = 2)

    if first_found and second_found:
        c_img = line_line_intersection(first_line, second_line)
        cv2.circle(disp_img, c_img, 5, _KULER_BLUE,2)
        get_major_end_pts(first_line, img_bw_u8)


    cv2.imshow("mask", mask.astype(np.uint8)*255)
    # cv2.imshow('edges_full', edge_img)
    # cv2.imshow('edges', edge_img_m)
    cv2.imshow('bw', img_bw_u8)
    return (disp_img, first_line, second_line, first_line_polar, second_line_polar)

def get_major_end_pts(first_line, img_bw):
    filter_kernel = np.ones((5,5))

    resp = cv2.filter2D(img_bw, cv2.CV_8U, filter_kernel)
    print resp
    print resp.shape
    cv2.imshow('resp', resp)
    print img_bw.shape
    print img_bw.dtype

    min_x_loc = []
    max_x_loc = []
    min_y_loc = []
    max_y_loc = []

    pts = []

    y_start = _END_SEARCH_EDGE_BUFFER
    y_end = img_bw.shape[0] - _END_SEARCH_EDGE_BUFFER
    x_start =  _END_SEARCH_EDGE_BUFFER
    x_end = img_bw.shape[1] - _END_SEARCH_EDGE_BUFFER


    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            if img_bw[y,x] != 0:
                continue
            else:
                img_bw[y,x] = 128

    cv2.imshow('filled', img_bw)

    return pts

def line_line_intersection(a, b):
    a1_x = a[0][0]
    a1_y = a[0][1]
    a2_x = a[1][0]
    a2_y = a[1][1]
    b1_x = b[0][0]
    b1_y = b[0][1]
    b2_x = b[1][0]
    b2_y = b[1][1]
    denom = (a1_x - a2_x)*(b1_y - b2_y) - (a1_y - a2_y)*(b1_x - b2_x)
    if denom == 0: # Parallel lines
        return None
    pt_x = ((a1_x*a2_y - a1_y*a2_x)*(b1_x-b2_x) -
                    (a1_x - a2_x)*(b1_x*b2_y - b1_y*b2_x))/denom
    pt_y = ((a1_x*a2_y - a1_y*a2_x)*(b1_y-b2_y) -
                    (a1_y - a2_y)*(b1_x*b2_y - b1_y*b2_x))/denom
    pt = (pt_x,pt_y)
    print pt
    return pt

def data_association(pts):
    pass

def estimate_transformation(pts_a, pts_b):
    pass

def transform_pts(pts_a, pts_b, transform):
    pass

def get_state(pts):
    pass

def get_reward(state):
    pass

def int_img2float(img_in):
    img_out = img_in.astype(np.float32)
    img_out *= 1./255
    return img_out

def get_y_img(img_in):
    y_abs_img = np.abs(img_in[:,:,_R_INDEX]*0.5 - img_in[:,:,_G_INDEX]*0.5)
    y_img = (img_in[:,:,_R_INDEX]*0.5 + img_in[:,:,_G_INDEX]*0.5) - y_abs_img - img_in[:,:,_B_INDEX]
    return y_img
