"""Smoke tests for the initial project scaffold."""

import unittest

from mini_redis import MiniRedis
from mini_redis.hash_map import HashMap
from mini_redis.linked_list import DoublyLinkedList, LinkedListNode
from mini_redis.min_heap import MinHeap


class ProjectStructureTests(unittest.TestCase):
    def test_core_types_can_be_constructed(self):
        database = MiniRedis()
        hash_map = HashMap()
        linked_list = DoublyLinkedList()
        node = LinkedListNode("sample")
        heap = MinHeap()

        self.assertIsInstance(database, MiniRedis)
        self.assertEqual(hash_map.size(), 0)
        self.assertEqual(len(linked_list), 0)
        self.assertEqual(node.data, "sample")
        self.assertEqual(heap.size(), 0)

    def test_unknown_command_uses_redis_style_error(self):
        result = MiniRedis().execute(["HELLO"])

        self.assertEqual(result, ["(error) ERR unknown command 'HELLO'"])


if __name__ == "__main__":
    unittest.main()
