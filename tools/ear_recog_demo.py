#!/usr/bin/env python

# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""
import linecache
import _init_paths
from lib.fast_rcnn.config import cfg
from lib.fast_rcnn.test import im_detect
from lib.utils.nms import nms
from lib.utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse
from OP_methods.BING_Objectness.source.bing_demo import bing_demo

count = 0
CLASSES = ('__background__', 'ear')

NETS = {'vgg16': ('VGG16',
                  'vgg16_fast_rcnn_iter_40000.caffemodel'),
        'vgg_cnn_m_1024': ('VGG_CNN_M_1024',
                           'vgg_cnn_m_1024_fast_rcnn_iter_40000.caffemodel'),
        'caffenet': ('CaffeNet',
                     'caffenet_fast_rcnn_iter_40000.caffemodel')}


def vis_detections(im, class_name, dets, thresh=0.8):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        print('\nNo {} detected'.format(class_name))
        return

    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')
    for i in inds:
        bbox = dets[i, :4]
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
        )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=12, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                 fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.draw()


def visualise(im, class_name, dets, thresh=0.8):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        print('\nNo {} detected'.format(class_name))
        cv2.imshow('{} detections with p({} | box) >= {:.1f}'.format(
            class_name, class_name, thresh), im)
        return
    for i in inds:
        bbox = dets[i, :4]
        score = dets[i, -1]

        cv2.rectangle(im, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(im, '{:s} {:.3f}'.format(class_name, score),
                    (int(bbox[0]), int(bbox[1] - 2)), font, 1, (0, 255, 0), 1)
    cv2.imshow('{} detections with p({} | box) >= {:.1f}'.format(
        class_name, class_name, thresh), im)


def ROI_boxes(matlab, image_filepath, cmd):
    if cmd == 'ed':
        print('Using edge_detector OP_method')
        # add the matlab directory path
        matlab.eval("cd('/home/harrysocool/Github/fast-rcnn/OP_methods/edges')")
        matlab.eval("addpath(genpath('/home/harrysocool/Github/fast-rcnn/OP_methods/edges'))")
        # matlab.eval("toolboxCompile")
        matlab.eval("res = edge_detector_demo('{}','{}',{},{})".format(image_filepath, 'EAR0.4_2', 0.55, 0.75))
        raw_boxes = matlab.get('res')
        boxes = np.asarray(raw_boxes)
    elif cmd == 'ss':
        print('Using selective_search OP_method')
        # selective_search OP_method
        matlab.eval("cd('/home/harrysocool/Github/fast-rcnn/OP_methods/selective_search_ijcv_with_python')")
        matlab.eval(
            "addpath(genpath('/home/harrysocool/Github/fast-rcnn/OP_methods/selective_search_ijcv_with_python'))")
        matlab.eval("res = selective_search_demo('{}')".format(image_filepath))
        raw_boxes = matlab.get('res')
        boxes = np.asarray(raw_boxes)
    elif cmd == 'BING':
        print('Using BING OP_method')
        # BING method
        boxes, _ = bing_demo(image_filepath)
    else:
        raise NameError('Wrong ROI OP_methods name. (CHOOSE FROM: ss, ed, BING)')

    return boxes


def demo(net, matlab, image_filepath, classes, args):
    """Detect object classes in an image using pre-computed object proposals."""
    timer = Timer()
    timer.tic()
    # Load pre-computed Selected Search object proposals
    obj_proposals = ROI_boxes(matlab, image_filepath, args.OP_method)
    if len(obj_proposals)==0:
        return

    # Load the demo image
    im = cv2.imread(image_filepath)

    # Detect all object classes and regress object bounds

    scores, boxes = im_detect(net, im, obj_proposals)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls in classes:
        cls_ind = CLASSES.index(cls)
        cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        keep = np.where(cls_scores >= CONF_THRESH)[0]
        cls_boxes = cls_boxes[keep, :]
        cls_scores = cls_scores[keep]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        if (len(dets) == 0):
            global count
            count += 1
            print('{} No Ear detected').format(count)
        # print 'All {} detections with p({} | box) >= {:.1f}'.format(cls, cls,
        #                                                             CONF_THRESH)
        if args.video_mode:
            visualise(im, cls, dets, thresh=CONF_THRESH)
        elif args.image_path is not None:
            vis_detections(im, cls, dets, thresh=CONF_THRESH)


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Train a Fast R-CNN network')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        choices=NETS.keys(), default='vgg16')
    parser.add_argument('--image', dest='image_path', help='the image path for detection',
                        default=None, type=str)
    parser.add_argument('--video', dest='video_mode',
                        help='Use video Frame or not(overides --image_index)',
                        action='store_true')
    parser.add_argument('--method', dest='OP_method', help='the ROI Object proposal method',
                        default=None, type=str)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    #
    cmd = args.OP_method

    if cmd == 'ss':
        model_dirname = '20160809_SS_train0.8'
    elif cmd == 'ed':
        model_dirname = '20160808_EAR0.4.2_train0.8'
    elif cmd == 'BING':
        model_dirname = '20160807_BING800_train0.8'
    else:
        raise IOError('Wrong cmd name, choose from ss, ed, BING')

    prototxt = os.path.join(cfg.ROOT_DIR, 'models', NETS[args.demo_net][0],
                            'test.prototxt')
    caffemodel = os.path.join(cfg.ROOT_DIR, 'output', model_dirname, 'soton_ear',
                              NETS[args.demo_net][1])

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/scripts/'
                       'fetch_fast_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        pass
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\nLoaded network {:s}'.format(caffemodel)

    # initialize the MATLAB server
    print '\nMATLAB Connected'
    import matlab_wrapper

    matlab = matlab_wrapper.MatlabSession()
    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'

    if args.image_path is None:
        for index in range(1, 548, 1):
            args.image_index = index
            if args.video_mode:
                image_filepath = os.path.join(cfg.ROOT_DIR, 'ear_recognition', 'data_file', 'video_frame.jpg')
                vc = cv2.VideoCapture(0)
                if vc.isOpened():  # try to get the first frame
                    rval, frame = vc.read()
                else:
                    rval = False

                while rval:
                    rval, frame = vc.read()
                    cv2.imwrite(image_filepath, frame)
                    key = cv2.waitKey(20)
                    if key == 27:  # exit on ESC
                        break
                    demo(net, matlab, image_filepath, ('ear',), args)
            else:
                index_csv_path = os.path.join(cfg.ROOT_DIR, 'ear_recognition', 'data_file', 'image_index_list.csv')
                image_filepath = linecache.getline(index_csv_path, args.image_index).strip('\n')
                # print(image_filepath)
                demo(net, matlab, image_filepath, ('ear',), args)
                # plt.show()
    else:
        image_filepath = args.image_path
        demo(net, matlab, image_filepath, ('ear',), args)
        plt.show()
        # fig = plt.figure()
        # fig.savefig('/home/harrysocool/Pictures/result_1.png', dpi=fig.dpi)