"""Tests for the optional bonus structures and Pub/Sub commands."""

import random
import unittest

from mini_redis import MiniRedis
from mini_redis.binary_tree import BinaryTree
from mini_redis.bst import BinarySearchTree
from mini_redis.dynamic_array import DynamicArray
from mini_redis.min_heap import MinHeap
from mini_redis.pubsub import PubSub, Subscriber


class DynamicArrayTests(unittest.TestCase):
    def test_append_doubles_capacity(self):
        array = DynamicArray(capacity=2)
        capacities = []
        for value in range(5):
            array.append(value)
            capacities.append(array.capacity)

        self.assertEqual(capacities, [2, 2, 4, 4, 8])
        self.assertEqual([array.get(i) for i in range(len(array))], [0, 1, 2, 3, 4])

    def test_set_remove_and_bounds(self):
        array = DynamicArray()
        for value in "abcd":
            array.append(value)
        array.set(0, "z")

        self.assertEqual(array.remove(1), "b")
        self.assertEqual(array.pop(), "d")
        self.assertEqual([array[i] for i in range(len(array))], ["z", "c"])
        with self.assertRaises(IndexError):
            array.get(2)
        with self.assertRaises(IndexError):
            array.get(-1)

    def test_heap_is_backed_by_dynamic_array(self):
        heap = MinHeap()
        for value in [5, 1, 4, 2, 3, 9, 7, 8, 6]:
            heap.push(value)

        self.assertIsInstance(heap.items, DynamicArray)
        self.assertEqual([heap.pop() for _ in range(9)], list(range(1, 10)))


class BinaryTreeTests(unittest.TestCase):
    def test_traversals_of_heap_shaped_tree(self):
        #        1
        #      2   3
        #     4 5 6
        tree = BinaryTree.from_array([1, 2, 3, 4, 5, 6])

        self.assertEqual(tree.preorder(), [1, 2, 4, 5, 3, 6])
        self.assertEqual(tree.inorder(), [4, 2, 5, 1, 6, 3])
        self.assertEqual(tree.postorder(), [4, 5, 2, 6, 3, 1])
        self.assertEqual(tree.level_order(), [1, 2, 3, 4, 5, 6])

    def test_heap_storage_level_order_matches_array(self):
        heap = MinHeap()
        for value in [9, 4, 7, 1, 8]:
            heap.push(value)
        storage = [heap.items[i] for i in range(heap.size())]

        self.assertEqual(BinaryTree.from_array(storage).level_order(), storage)

    def test_empty_tree(self):
        tree = BinaryTree.from_array([])
        self.assertEqual(tree.preorder() + tree.level_order(), [])


class BinarySearchTreeTests(unittest.TestCase):
    def test_insert_search_and_sorted_order(self):
        bst = BinarySearchTree()
        for value in [50, 30, 70, 20, 40, 60, 80]:
            self.assertTrue(bst.insert(value))

        self.assertFalse(bst.insert(40))
        self.assertTrue(bst.search(60))
        self.assertFalse(bst.search(65))
        self.assertEqual(bst.sorted_values(), [20, 30, 40, 50, 60, 70, 80])

    def test_delete_leaf_one_child_two_children_and_root(self):
        bst = BinarySearchTree()
        for value in [50, 30, 70, 20, 40, 60, 80, 65]:
            bst.insert(value)

        self.assertTrue(bst.delete(20))   # leaf
        self.assertTrue(bst.delete(60))   # one child
        self.assertTrue(bst.delete(70))   # two children (65, 80)
        self.assertTrue(bst.delete(50))   # root with two children
        self.assertFalse(bst.delete(999))
        self.assertEqual(bst.sorted_values(), [30, 40, 65, 80])
        self.assertEqual(bst.size(), 4)

    def test_random_operations_match_sorted_reference(self):
        rng = random.Random(20260923)
        bst = BinarySearchTree()
        reference = []
        for _ in range(300):
            value = rng.randrange(50)
            if rng.random() < 0.6:
                self.assertEqual(bst.insert(value), value not in reference)
                if value not in reference:
                    reference.append(value)
            else:
                self.assertEqual(bst.delete(value), value in reference)
                if value in reference:
                    reference.remove(value)
            self.assertEqual(bst.sorted_values(), sorted(reference))


class PubSubTests(unittest.TestCase):
    def test_each_subscriber_gets_its_own_queue(self):
        pubsub = PubSub()
        alice, bob = Subscriber(), Subscriber()
        pubsub.subscribe("news", alice)
        pubsub.subscribe("news", bob)
        pubsub.subscribe("news", bob)  # duplicate is ignored
        pubsub.subscribe("chat", bob)

        self.assertEqual(pubsub.publish("news", "hi"), 2)
        self.assertEqual(pubsub.publish("chat", "yo"), 1)
        self.assertEqual(pubsub.publish("empty", "x"), 0)
        self.assertEqual(alice.drain(), [("news", "hi")])
        self.assertEqual(bob.drain(), [("news", "hi"), ("chat", "yo")])
        self.assertEqual(bob.drain(), [])

    def test_cli_commands(self):
        db = MiniRedis()

        self.assertEqual(db.execute(["PUBLISH", "news", "early"]), ["(integer) 0"])
        self.assertEqual(
            db.execute(["SUBSCRIBE", "news", "chat"]),
            ['1) "subscribe"', '2) "news"', '3) (integer) 1',
             '1) "subscribe"', '2) "chat"', '3) (integer) 2'],
        )
        self.assertEqual(
            db.execute(["publish", "news", "hello world"]),
            ['(integer) 1', '1) "message"', '2) "news"', '3) "hello world"'],
        )
        self.assertEqual(
            db.execute(["SUBSCRIBE"]),
            ["(error) ERR wrong number of arguments for 'SUBSCRIBE' command"],
        )
        self.assertEqual(
            db.execute(["PUBLISH", "news"]),
            ["(error) ERR wrong number of arguments for 'PUBLISH' command"],
        )


if __name__ == "__main__":
    unittest.main()
