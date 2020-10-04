import unittest
import automaton_t
import sys, os

class TestVertex(unittest.TestCase):

    def test_add_edge(self):
        vertex = automaton_t.Vertex(0)
        vertex.add_edge("ab", 1)
        vertex.add_edge("12asADb-", 1)
        vertex.add_edge("ab", 0)
        self.assertEqual(vertex.edges, {"ab": set([0, 1]), "12asADb-": set([1])})

    def test_remove_edge(self):
        vertex = automaton_t.Vertex(0)
        vertex.add_edge("ab", 1)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 4)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 3)

        vertex.remove_edge("a", 0)
        self.assertEqual(vertex.edges, {"a": set([3, 4]), "ab": set([1])})

        vertex.remove_edge("a")
        self.assertEqual(vertex.edges, {"ab": set([1])})

        vertex.add_edge("a", 123)
        vertex.remove_edge("a", 123)
        self.assertEqual(vertex.edges, {"ab": set([1])})

    def test_neighbors_by_word(self):
        vertex = automaton_t.Vertex(0)
        vertex.add_edge("ab", 1)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 4)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 3)
        self.assertEqual(vertex.neighbors_by_word("a"), set([0, 3, 4]))

    def test_go(self):
        vertex = automaton_t.Vertex(0)
        vertex.add_edge("ab", 1)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 4)
        vertex.add_edge("a", 0)
        vertex.add_edge("a", 3)

        self.assertEqual(vertex.go("ab"), 1)
        self.assertRaises(KeyError, vertex.go, "b")


class TestAutomaton(unittest.TestCase):

    def test_getitem(self):
        automaton = automaton_t.Automaton()
        automaton[1]
        automaton[3]
        self.assertEqual(automaton._free_vertex_id, 4)
        self.assertEqual(set(automaton.vertices.keys()),  set([1, 3]))

    def test_add_edge(self):
        automaton = automaton_t.Automaton()
        automaton.add_edge(1, 2, "ab")
        self.assertEqual(set(automaton.vertices.keys()),  set([1, 2]))
        self.assertEqual(automaton[1].edges, {"ab": set([2])})

    def test_scan(self):
        automaton = automaton_t.Automaton()
        automaton.read_from_file('tests_input.txt')
        try:
            self.assertEqual(automaton[0].edges, {None: set([1])})
            self.assertEqual(automaton[1].edges, {'ab': set([1])})
            self.assertEqual(len(automaton.vertices), 2)
        except Exception:
            self.fail("Automaton.scan() didn't create vertex 0 or 1")

    def test_string(self):
        automaton = automaton_t.Automaton()
        automaton.add_edge(0, 1, 'asd')
        automaton[1].is_terminal = True
        automaton.add_edge(0, 2, None)

        try:
            with open(os.devnull, 'w') as output_file:
                sys.stdout = output_file
                print(automaton)
        except Exception:
            sys.stdout = sys.__stdout__
            self.fail('Automaton.__str__() raises an exception')
        sys.stdout = sys.__stdout__

    def test_accept_string(self):
        automaton = automaton_t.Automaton()
        automaton.add_edge(0, 1, 'a')
        automaton.add_edge(1, 0, 'b')
        automaton[0].is_terminal = True

        self.assertTrue(automaton.accept_string(''))
        self.assertTrue(automaton.accept_string('ab'))
        self.assertTrue(automaton.accept_string('ab' * 84))
        self.assertTrue(automaton.accept_string('ab' * 101))
        self.assertFalse(automaton.accept_string('a'))
        self.assertFalse(automaton.accept_string('b'))
        self.assertFalse(automaton.accept_string('ba'))
        self.assertFalse(automaton.accept_string('ab' * 10 + 'b'))

    def test_to_dfa(self, automaton=None):
        if automaton is None:
            automaton = automaton_t.Automaton()
        automaton.read_from_file('tests_input.txt')

        try:
            automaton.to_dfa()
        except Exception as e:
            self.fail("Automaton.to_dfa() raised an exception {0}".format(e))

        self.assertTrue(automaton.accept_string(''))
        self.assertTrue(automaton.accept_string('ab'))
        self.assertTrue(automaton.accept_string('ab' * 84))
        self.assertTrue(automaton.accept_string('ab' * 101))
        self.assertFalse(automaton.accept_string('a'))
        self.assertFalse(automaton.accept_string('b'))
        self.assertFalse(automaton.accept_string('ba'))
        self.assertFalse(automaton.accept_string('ab' * 10 + 'b'))

    def test_to_cdfa(self):
        automaton = automaton_t.Automaton()
        self.test_to_dfa(automaton)
        automaton.to_cdfa()
        for vertex in automaton.vertices.values():
            self.assertEqual(set(vertex.edges.keys()), automaton.alphabet)

    def test_reverse_cdfa(self):
        automaton = automaton_t.Automaton()
        automaton.read_from_file('tests_input.txt')

        automaton.to_dfa()
        automaton.to_cdfa()
        automaton.reverse_cdfa()

        self.assertFalse(automaton.accept_string(''))
        self.assertFalse(automaton.accept_string('ab'))
        self.assertFalse(automaton.accept_string('ab' * 84))
        self.assertFalse(automaton.accept_string('ab' * 101))
        self.assertTrue(automaton.accept_string('a'))
        self.assertTrue(automaton.accept_string('b'))
        self.assertTrue(automaton.accept_string('ba'))
        self.assertTrue(automaton.accept_string('ab' * 10 + 'b'))

        for vertex in automaton.vertices.values():
            self.assertEqual(set(vertex.edges.keys()), automaton.alphabet)

    def test_to_minimal_cdfa(self):
        automaton = automaton_t.Automaton()
        automaton.read_from_file('git_sample_test.txt')

        automaton.to_dfa()
        automaton.to_cdfa()
        automaton.to_minimal_cdfa()

        self.assertEqual(len(automaton.vertices), 5)

        self.assertTrue(automaton.accept_string(''))
        self.assertTrue(automaton.accept_string('ab'))
        self.assertTrue(automaton.accept_string('ab' * 84))
        self.assertTrue(automaton.accept_string('ab' * 101))
        self.assertTrue(automaton.accept_string('b'))
        self.assertFalse(automaton.accept_string('a'))
        self.assertFalse(automaton.accept_string('ba'))
        self.assertFalse(automaton.accept_string('ab' * 10 + 'b'))

        for vertex in automaton.vertices.values():
            self.assertEqual(set(vertex.edges.keys()), automaton.alphabet)

