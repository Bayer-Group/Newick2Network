"""Usage: newick2network.py <input_file> [<output_file>]

Process input_file, a Newick tree, into a csv file of nodes and a csv file
of edges.
Arguments:
  input_file    Newick tree file
  output_path   Destination dir for output (default: same dir as input)

Created by Lev Morgan <lev.l.morgan@nutraspace.com> github.com/levmorgan"""

import re
import os
import sys
import csv
from docopt import docopt
__author__ = 'Lev Morgan <lev.l.morgan@monsanto.com>'

class Newick2Network(object):
    def __init__(self, in_file_path, out_file_path):
        self.nodes = []
        self.edges = []
        self.internal_counter = 0
        self.in_file_path = in_file_path
        if not out_file_path:
            out_file_path = os.path.split(in_file_path)[0]
        self.out_file_path = out_file_path
        with open(in_file_path, "r") as infi:
            self.tokenizer = Tokenizer(infi)
            self.get_token = self.tokenizer.token_generator().next
            self.parse()

    def check_token(self, token, expected, regex=False):
        if regex and re.match(expected, token):
            return
        elif token == expected:
            return
        else:
            raise ValueError("Expected %s, got %s at %i:%i" % (expected, token,
                                                               self.tokenizer.line,
                                                               self.tokenizer.char))

    def parse(self):
        token, root, length = self.Branch(self.get_token())
        self.check_token(token, ";")
        try:
            token = self.get_token()
            raise(ValueError("Expected end of file, got %s" % (token)))
        except StopIteration:
            pass

        self.fix_internal_node_names()
        self.write_csv_output()

    def Branch(self, token):
        if token == "(":
            token, child = self.Internal(token)
        else:
            token, child = self.Leaf(token)
        token, length = self.Length(token)
        return token, child, length

    def Internal(self, token):
        self.check_token(token, "(")
        token, children = self.Branchset(self.get_token())
        self.check_token(token, ")")
        token, name = self.Name(self.get_token())
        if not name:
            name = "Internal%i" % (self.internal_counter)
            self.internal_counter += 1
        for child in children:
            self.nodes.append(child[0])
            self.edges.append([name, child[0], child[1]])

        return token, name

    def Branchset(self, token):
        children = []
        token, child, length = self.Branch(token)
        children.append((child, length))
        token, children_1 = self.Branchset_1(token)
        children.extend(children_1)
        return token, children

    def Branchset_1(self, token):
        children = []
        if token == ",":
            token = self.get_token()
            token, children = self.Branchset(token)
        return token, children

    def Leaf(self, token):
        return self.Name(token)

    def Name(self, token):
        if not re.match("[\w\-\.]", token):
            return token, ''
        name = []
        while re.match(r"[\w\-\.]", token):
            name.append(token)
            token = self.get_token()
        name = ''.join(name)
        return token, name

    def Length(self, token):
        length = None
        if token == ":":
            length = []
            token = self.get_token()
            while re.match(r"[\d\.E-]", token):
                length.append(token)
                token = self.get_token()
            if not length:
                self.check_token("token", "a number")
            length = ''.join(length)
            length = float(length)
        return token, length

    def fix_internal_node_names(self):
        max_internal = max([int(edge[0][8:]) for edge in self.edges])
        self.edges = [[self.fix_node_name(edge[0], max_internal), self.fix_node_name(edge[1], max_internal), edge[2]]
                      for edge in self.edges]

    def fix_node_name(self, name, max_):
        if name.startswith("Internal"):
            new_name = "Internal%i" % (-1*(int(name[8:])-max_))
            if new_name == "Internal0":
                return "Root"
            else:
                return new_name
        else:
            return name

    def write_csv_output(self):
        infi_name = os.path.split(os.path.splitext(self.in_file_path)[0])[1]
        outfi_format_string = os.path.join(self.out_file_path, infi_name + "_%s.csv")
        try:
            outfi_edges = open(outfi_format_string % ("edges"), "w")
            edges_writer = csv.writer(outfi_edges)
            [edges_writer.writerow(row) for row in self.edges]
            # outfi_nodes = open(outfi_format_string % ("nodes"), "w")
            # node_writer = csv.writer(outfi_nodes)
            # node_writer.writerow(self.nodes)
        except IOError as e:
            sys.stderr.write("Error: could not open output files for writing: %s" % (str(e)))


class Tokenizer(object):
    def __init__(self, input_file):
        self.line = 0
        self.char = 0
        self.input_file = input_file

    def token_generator(self):
        for i, line in enumerate(self.input_file):
            self.line = i
            for j, char in enumerate(line):
                self.char = j
                if re.match("\s", char):
                    pass
                else:
                    yield char


if __name__ == "__main__":
    arguments = docopt(__doc__)
    Newick2Network(arguments["<input_file>"], arguments["<output_file>"])