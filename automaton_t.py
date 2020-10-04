from vertex_t import Vertex
from collections import defaultdict


class Automaton:
    def __init__(self, start=0, vertices=dict(), alphabet=set(), other_automaton=None):
        if other_automaton is None:
            self.start = start
            self._free_vertex_id = (max(vertices) + 1) if len(vertices) else 0
            self.vertices = vertices
            self.alphabet = alphabet
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
        self.__getitem__(vertex_to)   # in order to add vertex_to in self.vertices
        self.__getitem__(vertex_from).add_edge(word, vertex_to)

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
            self.__getitem__(terminal_vertex_id).is_terminal = True

    def __str__(self):
        output = 'Automaton:\n'
        prefix = ' ' * 4
        output += prefix + 'Edges:\n'
        terminal_vertices = []

        for vertex in self.vertices:
            if self.__getitem__(vertex).is_terminal:
                terminal_vertices.append(vertex)
            for word, neighbors in self.__getitem__(vertex).edges.items():
                for vertex_to in neighbors:
                    output += prefix * 2 + 'From {0} to {1} by {2}\n'.format(vertex, vertex_to, word)

        output += prefix + 'Start state: {0}'.format(self.start)
        output += prefix + 'Terminal states: ' + ', '.join(str(v) for v in terminal_vertices) + '\n'
        return output

    def _split_long_edges(self): # replaces all edges with keys longer than 1 with multiple edges
        edges_to_delete = []
        for vertex_id in self.vertices:
            for word in self.__getitem__(vertex_id).edges:
                if word is not None and len(word) > 1:
                    edges_to_delete.append((vertex_id, word))

        for vertex_id, word in edges_to_delete:
            for edge_end in self.__getitem__(vertex_id).neighbors_by_word(word):
                last_vertex = vertex_id
                for i, letter in enumerate(word):
                    if i + 1 == len(word):
                        vertex_to = edge_end
                    else:
                        vertex_to = self._free_vertex_id
                        self._free_vertex_id += 1

                    self.add_edge(last_vertex, vertex_to, letter)
                    last_vertex = vertex_to
            self.__getitem__(vertex_id).remove_edge(word)

    def _shorten_path(self, vertex_from, word, visited_vertices): # dfs in wich every step except first is using null edge
        if word in vertex_from.edges:
            for vertex_to in vertex_from.edges[word]:
                if vertex_to not in visited_vertices:
                    visited_vertices.add(vertex_to)
                    self._shorten_path(self.__getitem__(vertex_to), None, visited_vertices)

    def _get_shortened_null_paths(self, vertex):
        new_edges = defaultdict(set)
        reached_by_null_edges = set()
        self._shorten_path(vertex, None, reached_by_null_edges)
        for vertex_to in reached_by_null_edges:
            for word in self.__getitem__(vertex_to).edges:
                if word is not None:
                    new_edges[word] |= self.__getitem__(vertex_to).edges[word]
        return new_edges

    def _remove_null_edges(self):
        for vertex in self.vertices.values():  # add new terminal vertices
            if not vertex.is_terminal:
                reached_by_null_edges = set()
                self._shorten_path(vertex, None, reached_by_null_edges)
                for terminal_vertex in reached_by_null_edges:
                    vertex.is_terminal |= self.__getitem__(terminal_vertex).is_terminal

        new_edges = dict()
        for vertex_id, vertex in self.vertices.items():  # add new adges and delete null edges
            new_edges[vertex_id] = self._get_shortened_null_paths(vertex)
        for vertex_id, edges in new_edges.items():
            vertex = self.__getitem__(vertex_id)
            if None in vertex.edges:
                del vertex.edges[None]
            for word, vertices_to in edges.items():
                vertex.edges[word] |= vertices_to

    def _reachable_from_vertex(self, current_vertex, visited):
        for neighbors in current_vertex.edges.values():
            for vertex_to in neighbors:
                if vertex_to not in visited:
                    visited.add(vertex_to)
                    self._reachable_from_vertex(self.__getitem__(vertex_to), visited)

    def _remove_duplicate_edges(self):
        new_automaton = Automaton(start=0, vertices=dict(), alphabet=set())   # idk why should I create new instance like that
        for subset in range(2**self._free_vertex_id):  # build automaton on subsets
            for vertex_id, vertex in self.vertices.items():
                if (2**vertex_id) & subset:
                    if self.start == vertex_id and (2**vertex_id) == subset:
                        new_automaton.start = subset
                    new_automaton[subset].is_terminal |= vertex.is_terminal
                    for word in vertex.edges:
                        new_automaton[subset].edges[word] |= vertex.edges[word]

        for subset in range(2**(self._free_vertex_id)):
            for word in new_automaton[subset].edges:
                subset_to = 0
                for vertex in new_automaton[subset].edges[word]:
                    subset_to += 2**vertex
                new_automaton[subset].edges[word] = {subset_to}

        useful_vertices = {new_automaton.start}
        new_automaton._reachable_from_vertex(new_automaton[new_automaton.start], useful_vertices)
        new_useful_vertex_id = {old_vertex_id: new_vertex_id
                                for new_vertex_id, old_vertex_id in enumerate(useful_vertices)}

        self.vertices = dict()
        self._free_vertex_id = len(useful_vertices)
        self.start = new_useful_vertex_id[new_automaton.start]
        for vertex in useful_vertices:
            self.__getitem__(new_useful_vertex_id[vertex]).is_terminal |= new_automaton[vertex].is_terminal
            for word, neighbors in new_automaton[vertex].edges.items():
                for vertex_to in neighbors:
                    self.add_edge(new_useful_vertex_id[vertex], new_useful_vertex_id[vertex_to], word)

    def to_dfa(self):
        self._split_long_edges()
        self._remove_null_edges()
        self._remove_duplicate_edges()

    def to_cdfa(self): # it is assumed that automaton is already deterministic
        missing_edges = []
        for vertex in self.vertices.values():
            missing_edges += [(vertex, letter) for letter in self.alphabet if letter not in vertex.edges]

        if missing_edges:
            dummy_vertex = self._free_vertex_id
            self._free_vertex_id += 1
            for vertex_from, letter in missing_edges:
                self.add_edge(vertex_from.id, dummy_vertex, letter)
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
        new_automaton = Automaton(start=group[self.start], alphabet=self.alphabet, vertices={})  # again idk
        for vertex in self.vertices.values():
            new_automaton[group[vertex.id]].is_terminal |= vertex.is_terminal
            for word in self.alphabet:
                new_automaton.add_edge(group[vertex.id], group[vertex.go(word)], word)
        self.__init__(other_automaton=new_automaton)
