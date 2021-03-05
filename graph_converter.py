#!/usr/bin/env python3

import os
from collections import defaultdict
import networkx as nx
import xml.etree.cElementTree as ElementTree
import xml.dom.minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    output = reparsed.toprettyxml(indent="\t", encoding="UTF-8")
    return output.decode("utf-8")


def save_graph_as_gxl(nxgraph, outfile, graphname=''):
    if not graphname:
        graphname = os.path.splitext(os.path.basename(outfile))[0]

    root = ElementTree.Element("gxl")
    graph = ElementTree.SubElement(root, "graph", edgeids="false", edgemode="undirected", id=graphname)

    for attr_name, attr_value in nxgraph.graph.items():
        a = ElementTree.SubElement(graph, "attr", name=attr_name)
        ElementTree.SubElement(a, type(attr_value).__name__).text = str(attr_value)

    for node_name, node_attr in nxgraph.node.items():
        node = ElementTree.SubElement(graph, "node", id='{}_{}'.format(graphname, node_name))
        assert 'pos' in node_attr
        x, y = node_attr['pos']
        a = ElementTree.SubElement(node, "attr", name="x")
        ElementTree.SubElement(a, "float").text = str(float(x))
        a = ElementTree.SubElement(node, "attr", name="y")
        ElementTree.SubElement(a, "float").text = str(float(y))

        for attr_name, attr_value in node_attr.items():
            # TODO: Rename 'pos' to x/y to be consistent
            assert attr_name != 'x'
            assert attr_name != 'y'
            if attr_name == 'pos':
                continue

            a = ElementTree.SubElement(node, "attr", name=attr_name)
            ElementTree.SubElement(a, "float").text = str(attr_value)
            # ElementTree.SubElement(a, type(attr_value).__name__).text = str(attr_value)

    edges = defaultdict(list)
    for e1 in nxgraph.edge:
        for e2 in nxgraph.edge[e1]:
            if e1 not in edges[e2]:
                if e2 not in edges[e1]:
                    edges[e1].append(e2)

    # edges = {e1: [e2 for e2 in nxgraph.edge[e1] if e1 <= e2] for e1 in nxgraph.edge}
    # edges = {k: v for k, v in edges.items() if v}
    for e1 in edges:
        for e2 in edges[e1]:
            ElementTree.SubElement(graph, "edge",
                                   attrib={"from": '{}_{}'.format(graphname, e1),
                                           "to": '{}_{}'.format(graphname, e2)})

    pretty = prettify(root)
    lines = pretty.split('\n')
    lines.insert(1, '<!DOCTYPE gxl SYSTEM "http://www.gupro.de/GXL/gxl-1.0.dtd">')

    with open(outfile, "w") as f:
        for line in lines:
            f.write('{}\n'.format(line))


def convert_yaml_to_gxl(infile, outfile, graphname=''):
    nxgraph = nx.read_yaml(infile)
    if not graphname:
        graphname = os.path.splitext(os.path.basename(infile))[0]

    save_graph_as_gxl(nxgraph, outfile, graphname)


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text


def load_gxl_to_graph(infile):
    nxgraph = nx.Graph()

    tree = ElementTree.parse(infile)
    root = tree.getroot()
    assert root.tag == 'gxl'
    assert len(root) == 1

    graph = root[0]
    assert graph.tag == 'graph'

    assert all(key in graph.attrib for key in ("edgeids", "edgemode", "id"))
    assert graph.attrib['edgeids'] == "false"
    assert graph.attrib['edgemode'] == "undirected"
    graphname = graph.attrib['id']
    nodeprefix = '{}_'.format(graphname)

    for elem in graph:
        if elem.tag == "attr":
            assert 'name' in elem.attrib
            attr_name = elem.attrib['name']
            assert len(elem) == 1
            attr_value = list(elem[0].itertext())[0]
            nxgraph.graph[attr_name] = attr_value

        elif elem.tag == "node":
            assert len(elem.attrib) == 1
            assert 'id' in elem.attrib
            node_name = int(remove_prefix(text=elem.attrib['id'], prefix=nodeprefix))
            # assert len(elem) == 2
            pos_dict = dict()
            for attr in elem:
                assert attr.tag == 'attr'
                assert 'name' in attr.attrib
                for attr_value in attr:
                    assert attr_value.tag == 'float'
                    value = float(list(attr_value.itertext())[0])
                    name = attr.attrib['name']
                    pos_dict[name] = value
            assert all(key in pos_dict for key in ('x', 'y'))
            pos = (pos_dict['x'], pos_dict['y'])
            nxgraph.add_node(node_name, pos=pos)

            for attr_name, attr_value in pos_dict.items():
                # TODO: Rename 'pos' to x/y to be consistent
                assert attr_name != 'pos'
                if attr_name in ('x', 'y'):
                    continue
                nxgraph.node[node_name][attr_name] = attr_value

        elif elem.tag == "edge":
            assert len(elem.attrib) == 2
            assert all(key in elem.attrib for key in ('to', 'from'))
            e1 = int(remove_prefix(text=elem.attrib['from'], prefix=nodeprefix))
            e2 = int(remove_prefix(text=elem.attrib['to'], prefix=nodeprefix))
            nxgraph.add_edge(e1, e2)

    nxgraph = nxgraph.to_undirected()
    nxgraph.graph['sourceGXL'] = os.path.abspath(infile)

    return nxgraph


def convert_gxl_to_yaml(infile, outfile):
    nxgraph = load_gxl_to_graph(infile)
    nx.write_yaml(nxgraph, outfile)
