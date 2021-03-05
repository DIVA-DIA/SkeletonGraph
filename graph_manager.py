#!/usr/bin/env python3

import itertools
import operator
from collections import defaultdict

import networkx as nx
import numpy as np
import scipy
import scipy.signal
from scipy.ndimage import measurements

import graph_converter
from binarize_manager import invert_image


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_endpoints_and_junctions(skeleton):
    a = invert_image(skeleton)
    b = np.matrix([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
    c = scipy.signal.convolve2d(a, b, 'same')
    d = np.multiply(a, c)

    endpoints = []
    possible_junctions = []
    for index, value in np.ndenumerate(d):
        if value > 2:
            possible_junctions.append(index)
        elif value == 1:
            endpoints.append(index)

    # clean junction points
    junctions = []
    for point in possible_junctions:
        found_better = False
        for neighbor in get_neighbor_points(point[0], point[1]):
            if neighbor in junctions:
                if d[neighbor] <= d[point]:
                    junctions.remove(neighbor)
                else:
                    found_better = True
        if not found_better:
            junctions.append(point)

    return endpoints, junctions, possible_junctions


def get_neighbor_points(y, x):
    result = list()
    result.append((y - 1, x - 1))
    result.append((y - 1, x))
    result.append((y - 1, x + 1))
    result.append((y, x - 1))
    result.append((y, x + 1))
    result.append((y + 1, x - 1))
    result.append((y + 1, x))
    result.append((y + 1, x + 1))
    return result


def get_previous_points(y, x):
    result = list()
    result.append((y - 1, x - 1))
    result.append((y - 1, x))
    result.append((y - 1, x + 1))
    result.append((y, x - 1))
    result.append((y + 1, x - 1))
    return result


def get_following_points(y, x):
    result = list()
    result.append((y, x + 1))
    result.append((y + 1, x - 1))
    result.append((y + 1, x))
    result.append((y + 1, x + 1))
    result.append((y - 1, x + 1))
    return result


def find_next_point(img, point):
    _BLACK = 0
    _WHITE = 1

    # TODO: Write your own iterator
    neighbor_and_distance = [(tuple(map(operator.add, point, (-1, -1))), 1.41),
                             (tuple(map(operator.add, point, (-1, 0))), 1.0),
                             (tuple(map(operator.add, point, (-1, 1))), 1.41),
                             (tuple(map(operator.add, point, (0, 1))), 1.0),
                             (tuple(map(operator.add, point, (1, 1))), 1.41),
                             (tuple(map(operator.add, point, (1, 0))), 1.0),
                             (tuple(map(operator.add, point, (1, -1))), 1.41),
                             (tuple(map(operator.add, point, (0, -1))), 1.0)]

    for neighbor, distance in neighbor_and_distance:
        try:
            if img[neighbor] == _BLACK:
                return neighbor, distance
        except IndexError:
            pass
    else:
        return point, 0


def find_path(img, start_point, step_length):
    _BLACK = 0
    _WHITE = 1

    list_points = [start_point]
    cur_delta = 0.0

    cur_point = start_point
    img[cur_point] = _WHITE

    while True:
        next_point, distance = find_next_point(img, cur_point)
        if not distance:
            break

        cur_delta += distance
        img[next_point] = _WHITE
        cur_point = next_point
        if cur_delta >= step_length:
            list_points.append(cur_point)
            cur_delta = 0.0

    if cur_point not in list_points:
        list_points.append(cur_point)

    return list_points, img


def count_neighbor_values(img, point, count_zero=False):
    neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
    result_dict = defaultdict(int)
    for neighbor in neighbors:
        value = img[tuple(map(operator.add, point, neighbor))]
        if value or count_zero:
            result_dict[value] += 1
    return result_dict


def list_neighbor_values(img, point, count_zero=False):
    neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
    result_list = list()
    for neighbor in neighbors:
        try:
            value = img[tuple(map(operator.add, point, neighbor))]
        except IndexError:
            pass
        else:
            if value or count_zero:
                result_list.append(value)
    return result_list


def skeleton_to_paths(skeleton, step_length):
    _BLACK = 0
    _WHITE = 1

    endpoints, junctions, possible_junctions = get_endpoints_and_junctions(skeleton)

    # Remove junction points from image
    img_no_junctions = np.copy(skeleton)
    for junction in possible_junctions:
        img_no_junctions[junction] = _WHITE

    # Junction image
    junction_image = np.ones_like(skeleton)
    for junction in possible_junctions:
        junction_image[junction] = _BLACK

    img_junction_labels, num = measurements.label(invert_image(junction_image), structure=np.ones((3, 3)))

    junction_groups = [[] for x in range(num)]
    for index, value in np.ndenumerate(img_junction_labels):
        if value:
            junction_groups[value - 1].append(index)

    junction_points = [tuple([int(round(sum(y) / float(len(y)), 0)) for y in zip(*x)]) for x in junction_groups]

    endpoints_temp, _, _ = get_endpoints_and_junctions(img_no_junctions)

    neighbor_junction = dict()
    ignore_endpoints = list()
    junction_paths = list()
    ep_other = list()
    for point in endpoints_temp:
        neighbor_values = list_neighbor_values(img_junction_labels, point, count_zero=False)
        if len(neighbor_values) == 1:
            neighbor_junction[point] = junction_points[neighbor_values[0] - 1]
        elif len(neighbor_values) == 2:
            ignore_endpoints.append(point)
            junction_paths.append([junction_points[neighbor_values[0] - 1], junction_points[neighbor_values[1] - 1]])
        else:
            ep_other.append(point)  # no junction nearby

    ep_next_to_junction = sorted(list(neighbor_junction.keys()), key=lambda element: (element[1], element[0]))
    ep_other = sorted(ep_other, key=lambda element: (element[1], element[0]))

    temp_img = np.copy(img_no_junctions)
    list_of_paths = list()
    for ep in itertools.chain(ep_next_to_junction, ep_other):
        if ep not in ignore_endpoints:
            path, temp_img = find_path(img=temp_img, start_point=ep, step_length=step_length)
            if path[0] in neighbor_junction:
                path.insert(0, neighbor_junction[path[0]])
            if path[-1] in neighbor_junction:
                path.append(neighbor_junction[path[-1]])
            list_of_paths.append(path)
        else:
            temp_img[ep] = _WHITE

    list_of_paths.extend(junction_paths)

    # Find missing areas aka circles
    circles, num = measurements.label(invert_image(temp_img), structure=np.ones((3, 3)))

    if not num:
        circle_start_points = list()
    else:
        circle_start_points = [None for x in range(num)]
        for index, value in np.ndenumerate(circles):
            if value:
                cur_point = circle_start_points[value - 1]
                if cur_point:
                    if cur_point[1] > index[1]:
                        circle_start_points[value - 1] = index
                    if cur_point[1] == index[1]:
                        if cur_point[0] > index[0]:
                            circle_start_points[value - 1] = index
                else:
                    circle_start_points[value - 1] = index

    # Add circle paths
    for cs in circle_start_points:
        path, temp_img = find_path(img=temp_img, start_point=cs, step_length=step_length)
        # Build circle: Replace last element of path with the start element to create a circle
        path = path[:-1] + path[0:1]
        list_of_paths.append(path)

    list_of_paths = [[point for point in path if point not in ep_next_to_junction] for path in list_of_paths]

    return list_of_paths


def create_graph_from_paths(list_of_paths, **kwargs):
    # create set of nodes:
    points = sorted(list({point for path in list_of_paths for point in path}),
                    key=lambda element: (element[1], element[0]))
    node_id_to_point = {node_id: point for node_id, point in enumerate(points)}
    point_to_node_id = {point: node_id for node_id, point in node_id_to_point.items()}
    list_of_id_paths = [[point_to_node_id[point] for point in path] for path in list_of_paths]

    # print("\n\n==== PATHS: =========================\n")
    # pprint(list_of_id_paths)

    graph = nx.Graph(**kwargs)

    # Add all nodes
    pos_of_nodes = {node_id: (x, y) for node_id, (y, x) in node_id_to_point.items()}
    for node_id, pos in pos_of_nodes.items():
        graph.add_node(node_id, pos=pos)

    # Add all edges
    for path in list_of_id_paths:
        for v, w in pairwise(path):
            graph.add_edge(v, w)
    graph = graph.to_undirected()

    return graph


def write_graph_to_yaml(graph, outfile):
    nx.write_yaml(graph, outfile)


def write_graph_to_gxl(graph, outfile):
    graph_converter.save_graph_as_gxl(nxgraph=graph, outfile=outfile)

