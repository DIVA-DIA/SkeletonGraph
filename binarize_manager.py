#!/usr/bin/env python3

import os
import warnings

import numpy as np
import scipy
import scipy.ndimage.filters
import scipy.signal
import skimage
import skimage.filters
import skimage.io
import skimage.morphology


def difference_of_gaussians(img, sigma1, sigma2):
    """
    Difference of Gaussians
    :param img: Image object
    :param sigma1: Sigma for first Gaussian
    :param sigma2: Sigma for second Gaussian
    :return: Image object (Gaussian2 - Gaussian1)
    """
    blur1 = skimage.filters.gaussian(img, sigma1)
    blur2 = skimage.filters.gaussian(img, sigma2)
    return blur2 - blur1


def invert_image(img):
    """
    Inverts an image object
    :param img: Image object
    :return: Inverted image object
    """
    return 1 - img


def apply_threshold(img, threshold):
    return img > threshold


def fix_small_holes(image):
    fixed_image = np.copy(image)

    a = invert_image(image)
    b = np.matrix([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
    c = scipy.signal.convolve2d(a, b, 'same')
    # d = np.multiply(image, c)

    # for index, value in np.ndenumerate(d):
    for index, value in np.ndenumerate(c):
        if value >= 7:
            fixed_image[index] = 0
        if value <= 1:
            fixed_image[index] = 1

    return fixed_image


def img_to_binary(img, sigma1, sigma2, threshold):
    if (not sigma1) or (sigma1 <= 0):
        raise ValueError("sigma1 must be a positive number [sigma1={sigma1}]".format(sigma1=sigma1))
    if (not sigma2) or (sigma2 <= 0):
        raise ValueError("sigma2 must be a positive number [sigma2={sigma2}]".format(sigma2=sigma2))
    if (not threshold) or (0.0 >= threshold <= 1.0):
        raise ValueError(
            "threshold must be a number between 0.0 and 1.0 [threshold={threshold}]".format(threshold=threshold))

    edge_image = invert_image(difference_of_gaussians(img, sigma1, sigma2))
    binary_image = apply_threshold(edge_image, threshold)
    return binary_image


def makedirs_for_file(path):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)


def binary_to_skeleton(binary_image):
    skeleton = invert_image(skimage.morphology.skeletonize(invert_image(binary_image)))
    return skeleton


def write_binary_file(binary_image, outfile):
    makedirs_for_file(outfile)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        skimage.io.imsave(outfile, skimage.img_as_ubyte(binary_image))


def write_skeleton_file(skeleton, outfile):
    makedirs_for_file(outfile)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        skimage.io.imsave(outfile, skeleton * 255)
