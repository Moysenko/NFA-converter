from collections import defaultdict


class Vertex:
    def __init__(self, vertex_id, is_terminal=False):
        self.is_terminal = is_terminal
        self.id = vertex_id
        self.edges = defaultdict(set)

    def __hash__(self):
        return hash(self.id)

    def add_edge(self, word, vertex_to):
        self.edges[word].add(vertex_to)

    def remove_edge(self, word, vertex_to=None):
        if vertex_to is not None:
            self.edges[word].remove(vertex_to)
        else:
            del self.edges[word]

    def neighbors_by_word(self, word):
        return self.edges[word]

    def go(self, word): # to make it convenient to step in DFA
        if word not in self.edges:
            raise KeyError("Vertex {0} doesn't have edge with key {1}".
                           format(self.id, word))
        return list(self.edges[word])[0]


