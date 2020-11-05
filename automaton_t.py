from vertex_t import Vertex
from collections import defaultdict, namedtuple
import sys, os
import json

class Automaton:
    def __init__(self, start=0, vertices=None, alphabet=None, other_automaton=None):
        if other_automaton is None:
            self.start = start
            self.vertices = vertices or dict()
            self._free_vertex_id = (max(self.vertices) + 1) if len(self.vertices) else 0
            self.alphabet = alphabet or set()
        else:
            self.start = other_automaton.start
            self._free_vertex_id = other_automaton._free_vertex_id
            self.vertices = dict(other_automaton.vertices)
            self.alphabet = other_automaton.alphabet.copy()

    def __getitem__(self, vertex_id):
        if vertex_id not in self.vertices:
            self._free_vertex_id = max(self._free_vertex_id, vertex_id + 1)
            self.vertices[vertex_id] = Vertex(vertex_id)
        return self.vertices[vertex_id]

    def add_edge(self, vertex_from, vertex_to, word):
        self[vertex_to]   # in order to add vertex_to in self.vertices
        self[vertex_from].add_edge(word, vertex_to)

    def scan(self):
        self.alphabet = set(input('Alphabet: '))

        number_of_edges = int(input('Number of edges: '))
        print('Edges:      (in format "{from} {to} {word}", symbol "-" stands for empty string)')
        self.vertices = dict()
        self._free_vertex_id = 0
        for edge_id in range(number_of_edges):
            vertex_from, vertex_to, word = input('Edge #{0}: '.format(edge_id)).split()
            if word == '-':  # null edge
                word = None
            self.add_edge(int(vertex_from), int(vertex_to), word)

        self.start = int(input('Start state: '))
        for terminal_vertex_id in list(map(int, input('Terminal states: ').split())):
            self[terminal_vertex_id].is_terminal = True

    def read_from_file(self, filename):
        with open(filename, 'r') as input_file, open(os.devnull, 'w') as output_file:
            sys.stdin = input_file
            sys.stdout = output_file
            self.scan()
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

    def __str__(self):
        output = 'Automaton:\n'
        prefix = ' ' * 4
        output += prefix + 'Edges:\n'
        terminal_vertices = []

        for vertex in self.vertices:
            if self[vertex].is_terminal:
                terminal_vertices.append(vertex)
            for word, neighbors in self[vertex].edges.items():
                for vertex_to in neighbors:
                    output += prefix * 2 + 'From {0} to {1} by {2}\n'.format(vertex, vertex_to, word or '-')

        output += prefix + 'Start state: {0}'.format(self.start)
        output += prefix + 'Terminal states: ' + ', '.join(str(v) for v in terminal_vertices) + '\n'
        return output

    def _split_long_edges(self):  # replaces all edges with keys longer than 1 with multiple edges
        edges_to_delete = []
        for vertex_id in self.vertices:
            for word in self[vertex_id].edges:
                if word is not None and len(word) > 1:
                    edges_to_delete.append((vertex_id, word))

        for vertex_id, word in edges_to_delete:
            for edge_end in self[vertex_id].neighbors_by_word(word):
                last_vertex = vertex_id
                for i, letter in enumerate(word):
                    if i + 1 == len(word):
                        vertex_to = edge_end
                    else:
                        vertex_to = self._free_vertex_id
                        self._free_vertex_id += 1

                    self.add_edge(last_vertex, vertex_to, letter)
                    last_vertex = vertex_to
            self[vertex_id].remove_edge(word)

    def _shorten_path(self, vertex_from, word, visited_vertices):  # dfs in wich every step except first is using null edge
        if word in vertex_from.edges:
            for vertex_to in vertex_from.edges[word]:
                if vertex_to not in visited_vertices:
                    visited_vertices.add(vertex_to)
                    self._shorten_path(self[vertex_to], None, visited_vertices)

    def _get_shortened_null_paths(self, vertex):
        new_edges = defaultdict(set)
        reached_by_null_edges = set()
        self._shorten_path(vertex, None, reached_by_null_edges)
        for vertex_to in reached_by_null_edges:
            for word in self[vertex_to].edges:
                if word is not None:
                    new_edges[word] |= self[vertex_to].edges[word]
        return new_edges

    def _remove_null_edges(self):
        for vertex in self.vertices.values():  # add new terminal vertices
            if not vertex.is_terminal:
                reached_by_null_edges = set()
                self._shorten_path(vertex, None, reached_by_null_edges)
                for terminal_vertex in reached_by_null_edges:
                    vertex.is_terminal |= self[terminal_vertex].is_terminal

        new_edges = dict()
        for vertex_id, vertex in self.vertices.items():  # add new adges and delete null edges
            new_edges[vertex_id] = self._get_shortened_null_paths(vertex)
        for vertex_id, edges in new_edges.items():
            vertex = self[vertex_id]
            if None in vertex.edges:
                del vertex.edges[None]
            for word, vertices_to in edges.items():
                vertex.edges[word] |= vertices_to

    def _reachable_from_vertex(self, current_vertex, visited):
        for neighbors in current_vertex.edges.values():
            for vertex_to in neighbors:
                if vertex_to not in visited:
                    visited.add(vertex_to)
                    self._reachable_from_vertex(self[vertex_to], visited)

    def _init_from_automaton_subsets(self, other):
        for subset in range(2**other._free_vertex_id):  # build automaton on subsets
            for vertex_id, vertex in other.vertices.items():
                if (2**vertex_id) & subset:
                    if other.start == vertex_id and (2**vertex_id) == subset:
                        self.start = subset
                    self[subset].is_terminal |= vertex.is_terminal
                    for word in vertex.edges:
                        self[subset].edges[word] |= vertex.edges[word]

    def _replace_edges_with_subsets(self):
        for vertex in self.vertices:
            for word in self[vertex].edges:
                subset_to = 0
                for vertex_to in self[vertex].edges[word]:
                    subset_to += 2**vertex_to
                self[vertex].edges[word] = {subset_to}

    def _init_from_useful_vertices(self, automaton):
        useful_vertices = {automaton.start}
        automaton._reachable_from_vertex(automaton[automaton.start], useful_vertices)
        useful_vertex_id = {old_vertex_id: vertex_id
                            for vertex_id, old_vertex_id in enumerate(useful_vertices)}

        self.vertices = dict()
        self._free_vertex_id = len(useful_vertices)
        self.start = useful_vertex_id[automaton.start]
        for vertex in useful_vertices:
            self[useful_vertex_id[vertex]].is_terminal |= automaton[vertex].is_terminal
            for word, neighbors in automaton[vertex].edges.items():
                for vertex_to in neighbors:
                    self.add_edge(useful_vertex_id[vertex], useful_vertex_id[vertex_to], word)

    def _remove_duplicate_edges(self):
        new_automaton = Automaton(start=0, vertices=dict(), alphabet=set())
        new_automaton._init_from_automaton_subsets(self)
        new_automaton._replace_edges_with_subsets()
        self._init_from_useful_vertices(new_automaton)

    def to_dfa(self):
        self._split_long_edges()
        self._remove_null_edges()
        self._remove_duplicate_edges()

    def accept_string(self, word):
        current_state = self.start
        for letter in word:
            try:
                current_state = self[current_state].go(letter)
            except KeyError:
                return False
        return self[current_state].is_terminal

    def to_cdfa(self):  # it is assumed that automaton is already deterministic
        missing_edges = []
        Edge = namedtuple('Edge', 'vertex, letter')
        for vertex in self.vertices.values():
            missing_edges += [Edge(vertex=vertex, letter=letter) for letter in self.alphabet if letter not in vertex.edges]

        if missing_edges:
            dummy_vertex = self._free_vertex_id
            self._free_vertex_id += 1
            for edge in missing_edges:
                self.add_edge(edge.vertex.id, dummy_vertex, edge.letter)
            for letter in self.alphabet:
                self.add_edge(dummy_vertex, dummy_vertex, letter)
            self._free_vertex_id += 1

    def reverse_cdfa(self):
        for vertex in self.vertices.values():
            vertex.is_terminal ^= 1

    def _equivalence_groups(self):
        group = dict()
        for vertex in self.vertices.values():
            group[vertex.id] = int(vertex.is_terminal)

        old_number_of_classes = 1
        current_number_of_classes = 2
        step_id = 0

        while old_number_of_classes != current_number_of_classes:
            step_id += 1

            output_groups = defaultdict(list)
            for vertex in self.vertices.values():
                key = tuple([group[vertex.id]] + [group[vertex.go(letter)] for letter in self.alphabet])
                output_groups[key].append(vertex.id)

            old_number_of_classes = current_number_of_classes
            current_number_of_classes = len(output_groups)

            group = dict()
            for group_id, vertices in enumerate(output_groups.values()):
                for vertex in vertices:
                    group[vertex] = group_id

        return group

    def to_minimal_cdfa(self):
        group = self._equivalence_groups()
        new_automaton = Automaton(start=group[self.start], alphabet=self.alphabet, vertices={})
        for vertex in self.vertices.values():
            new_automaton[group[vertex.id]].is_terminal |= vertex.is_terminal
            for word in self.alphabet:
                new_automaton.add_edge(group[vertex.id], group[vertex.go(word)], word)
        self.__init__(other_automaton=new_automaton)
