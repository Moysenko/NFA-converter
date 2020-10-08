# NFA-converter

Tool for converting nondeterministic finite automaton to deterministic finite automaton (DFA) / complete deterministic finite automaton (CDFA) / minimal CDFA.

***

## Usage 

**Automaton** object 
```python
class automaton_t.Automaton(start=0, vertices=dict(), alphabet=set(), other_automaton=None)  
```
Returns a new Automaton object. There are two ways to initialize it:
1. Initialize directly with a start state (*start*), set of alphabet elements (*alphabet*) and a dictionary like {state number: Vertex object} (*vertices*).
2. Initialize with another Automaton object (*other_automaton*). In this case all fields of other_automaton will be copied.

Automaton objects support the following methods:
  * **scan**()
    * Read the automaton from the terminal.
  * **add_edge**(*vertex_from, vertex_to, word*)
    * Add edge from *vertex_from* to *Vertex_to* with token = *word*.
  * **__getitem__**(*vertex_id*)
    * Return vertex from automaton with id = *vertex_id*. 
  * **__str__**():
    * String with automaton description.
  * **to_dfa**()
    * Convert automaton to deterministic finite automaton.
  * **to_cdfa**()
    * Convert automaton to complete deterministic finite automaton. It is assumed that finite automaton is already deterministic, otherwise the behavior is undefined.
  * **reverse_cdfa**()
    * Convert to reverse complete deterministic finite automaton. It is assumed that finite automaton is already complete deterministic, otherwise the behavior is undefined.
  * **to_minimal_cdfa**()
    * Convert to minimal complete deterministic finite automaton. It is assumed that finite automaton is already complete deterministic, otherwise the behavior is undefined.
    
---

**Vertex** object 
```python
class vertex_t.Vertex(vertex_id, is_terminal=False)
```
Vertex object has the following fields:
  * *is_terminal* - flag indicating that the vertex is terminal
  * *id* - vertex id
  * *edges* - collections.defaultdict like {token: [a list of vertices that can be reached from the current vertex along the edge with this token]}
  
Vertex objects have the following fields:
  * **add_edge**(*word, vertex_to*)
    * Add edge from vertex to *vertex_to* with token = *word*.
  * **remove_edge**(*word, vertex_to=None*)
    * Remove edge from vertex to *vertex_to* with token = *word*. If *vertex_to* is None than all edges with token = *word* will be deleted.
  * **neighbors_by_word**(*word*)
    * Vertices such that they can be reached from the current vertex along the edge with the token = *word*.
  * **go**(*word*)
    * Such a vertex that you can get to it from the current vertex along the edge with token = *word*. 

### Example

The following code reads the automaton from console and converts it to complete deterministic finite automaton
```python
import automaton_t
automaton = automaton_t.Automaton()
automaton.scan()
automaton.to_dfa()
automaton.to_cdfa()
automaton.to_minimal_cdfa()
print(automaton)
```

Example of input:
```
Alphabet: ab
Number of edges: 3
Edges:      (in format "{from} {to} {word}", symbol "-" stands for empty string)
Edge #0: 0 1 -
Edge #1: 1 1 ab
Edge #2: 0 2 b
Start state: 0
Terminal states: 1 2
```

Example of output:
```
Automaton:
    Edges:
        From 0 to 4 by a
        From 0 to 1 by b
        From 4 to 4 by a
        From 4 to 4 by b
        From 1 to 0 by a
        From 1 to 4 by b
        From 2 to 0 by a
        From 2 to 3 by b
        From 3 to 4 by a
        From 3 to 4 by b
    Start state: 2    Terminal states: 1, 2, 3
```

To run tests execute the following bash code in the repo directory:
```shell
coverage run -m unittest discover
coverage html
open htmlcov/index.html
```
