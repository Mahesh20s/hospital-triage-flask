"""Data structures built from scratch for the Hospital Triage project."""
from collections import deque


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    """Singly linked list with a tail pointer: O(1) append, ordered traversal."""

    def __init__(self):
        self.head = self.tail = None
        self.size = 0

    def append(self, data):
        node = Node(data)
        if self.tail:
            self.tail.next = node
        else:
            self.head = node
        self.tail = node
        self.size += 1

    def to_list(self):
        out, cur = [], self.head
        while cur:
            out.append(cur.data)
            cur = cur.next
        return out


class _TreeNode:
    def __init__(self, key, value):
        self.key, self.value = key, value
        self.left = self.right = None


class BST:
    """Binary search tree: sorted listing by in-order traversal, O(log n) average insert."""

    def __init__(self):
        self.root = None

    def insert(self, key, value):
        node = _TreeNode(key, value)
        if not self.root:
            self.root = node
            return
        cur = self.root
        while True:
            if key < cur.key:
                if cur.left is None:
                    cur.left = node
                    return
                cur = cur.left
            else:
                if cur.right is None:
                    cur.right = node
                    return
                cur = cur.right

    def in_order(self):
        out, stack, cur = [], [], self.root
        while stack or cur:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            out.append(cur.value)
            cur = cur.right
        return out


class Graph:
    """Undirected graph as an adjacency list; BFS gives the fewest-hops route."""

    def __init__(self):
        self.adj = {}

    def add_edge(self, a, b):
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set()).add(a)

    def nodes(self):
        return sorted(self.adj)

    def route(self, src, dst):
        if src not in self.adj or dst not in self.adj:
            return None
        parent, queue = {src: None}, deque([src])
        while queue:
            cur = queue.popleft()
            if cur == dst:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                return path[::-1]
            for nxt in sorted(self.adj[cur]):
                if nxt not in parent:
                    parent[nxt] = cur
                    queue.append(nxt)
        return None
