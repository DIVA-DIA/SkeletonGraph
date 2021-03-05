#!/usr/bin/env python3

import os
import argparse

import skimage
import matplotlib.pyplot as plt

import binarize_manager
import graph_manager


def display_graph(img, binary_image, skeleton, list_of_paths):
    # display results
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(20, 12),
                                                 sharex='all', sharey='all',
                                                 subplot_kw={'adjustable': 'box-forced'})
    ax1.imshow(img, cmap=plt.cm.gray, interpolation='none')
    ax1.axis('tight')
    ax1.set_aspect('equal')
    ax1.set_title('Original', fontsize=20)

    ax2.imshow(binary_image, cmap=plt.cm.gray, interpolation='none')
    ax2.axis('tight')
    ax2.set_aspect('equal')
    ax2.set_title('Binary', fontsize=20)

    ax3.imshow(skeleton, cmap=plt.cm.gray, interpolation='none')
    ax3.axis('tight')
    ax3.set_aspect('equal')
    ax3.set_title('Skeleton', fontsize=20)

    # ax4.imshow(skeleton, cmap=plt.cm.gray, interpolation='none')
    ax4.axis('tight')
    ax4.set_aspect('equal')
    ax4.set_title('Graph', fontsize=20)
    for path in list_of_paths:
        ax4.plot(*reversed(list(zip(*path))), c='b', linewidth=1)
        ax4.scatter(*reversed(list(zip(*path))), c='b', s=50)

    fig.tight_layout()

    plt.show()


def create_graph_example(path_img, sigma1=1, sigma2=30, threshold=0.87, step_length=25):
    # Load image
    with open(path_img, "rb") as f_in:
        img = skimage.io.imread(f_in, as_grey=True)

    # Binary
    binary_image = binarize_manager.img_to_binary(img, sigma1=sigma1, sigma2=sigma2, threshold=threshold)
    binary_image = binarize_manager.fix_small_holes(binary_image)

    # Skeleton
    skeleton = binarize_manager.binary_to_skeleton(binary_image)

    # Graph
    list_of_paths = graph_manager.skeleton_to_paths(skeleton, step_length=step_length)
    graph = graph_manager.create_graph_from_paths(list_of_paths)

    return img, binary_image, skeleton, list_of_paths, graph
    

def convert_to_binary(infile, outfile, sigma1=1, sigma2=30, threshold=0.87):
    with open(infile, "rb") as f_in:
        img = skimage.io.imread(f_in, as_grey=True)
    binary_image = binarize_manager.img_to_binary(img, sigma1=sigma1, sigma2=sigma2, threshold=threshold)
    binarize_manager.write_binary_file(binary_image=binary_image, outfile=outfile)


def main():
    parser = argparse.ArgumentParser(description='Skeleton Graph Example')
    parser.add_argument('-i', '--input', help='Path to input image', required=True)
    parser.add_argument('-d', '--display', action='store_true', help='Display output (default: False)', required=False)
    parser.add_argument('-o', '--output', help='Path to output file', required=False)

    args = parser.parse_args()

    if not args.display and not args.output:
        print('You should have -d/--display ("display output") or -o/--output ("path to output file") specified.')
        print('Otherwise, there is nothing to do. Canceling...')
        print('[Use -h/--help for help.]')
        exit()

    path_img = args.input
    if not path_img:
        print('No input file specified (-i/--input).')
        print('[Use -h/--help for help.]')
        exit()

    if not os.path.exists(path_img):
        print('Specified input file does not exist ({}).'.format(path_img))
        print('[Use -h/--help for help.]')
        exit()

    img, binary_image, skeleton, list_of_paths, graph = create_graph_example(path_img,
                                                                             sigma1=1, sigma2=30, threshold=0.87,
                                                                             step_length=10)
    
    if args.display:
        print('Displaying output images and graph')
        display_graph(img, binary_image, skeleton, list_of_paths)

    if args.output:
        print('Write output to "{}"'.format(args.output))
        graph_manager.write_graph_to_gxl(graph=graph, outfile=args.output)


if __name__ == '__main__':
    main()
