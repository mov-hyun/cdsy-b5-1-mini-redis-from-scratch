"""Unit tests for the custom minimum heap."""

import unittest

from mini_redis.min_heap import MinHeap


class MinHeapTests(unittest.TestCase):
    def test_empty_heap_returns_none(self):
        heap = MinHeap()

        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())
        self.assertEqual(heap.size(), 0)

    def test_push_places_smallest_item_at_root(self):
        heap = MinHeap()
        heap.push(8)
        heap.push(3)
        heap.push(5)
        heap.push(1)

        self.assertEqual(heap.peek(), 1)
        self.assertEqual(heap.size(), 4)

    def test_pop_returns_items_in_ascending_order(self):
        heap = MinHeap()
        values = [7, 2, 9, 1, 5, 3]

        for value in values:
            heap.push(value)

        popped = [heap.pop() for _ in range(len(values))]

        self.assertEqual(popped, [1, 2, 3, 5, 7, 9])
        self.assertEqual(heap.size(), 0)
        self.assertIsNone(heap.pop())

    def test_duplicate_values_are_preserved(self):
        heap = MinHeap()

        for value in [4, 2, 4, 2]:
            heap.push(value)

        self.assertEqual([heap.pop() for _ in range(4)], [2, 2, 4, 4])

    def test_pop_restores_heap_property(self):
        heap = MinHeap()

        for value in [1, 4, 2, 8, 5, 3, 7, 9, 6]:
            heap.push(value)

        self.assertEqual(heap.pop(), 1)
        self.assert_heap_property(heap)
        self.assertEqual(heap.pop(), 2)
        self.assert_heap_property(heap)

    def test_ttl_tuples_are_ordered_by_expiration_then_key(self):
        heap = MinHeap()
        heap.push((300.0, "user:3"))
        heap.push((100.0, "user:2"))
        heap.push((100.0, "user:1"))
        heap.push((200.0, "user:4"))

        self.assertEqual(heap.pop(), (100.0, "user:1"))
        self.assertEqual(heap.pop(), (100.0, "user:2"))
        self.assertEqual(heap.pop(), (200.0, "user:4"))
        self.assertEqual(heap.pop(), (300.0, "user:3"))

    def test_interleaved_push_and_pop(self):
        heap = MinHeap()
        heap.push(10)
        heap.push(20)
        self.assertEqual(heap.pop(), 10)

        heap.push(5)
        heap.push(15)

        self.assertEqual(heap.pop(), 5)
        self.assertEqual(heap.pop(), 15)
        self.assertEqual(heap.pop(), 20)

    def assert_heap_property(self, heap):
        for parent_index in range(heap.size()):
            left_index = parent_index * 2 + 1
            right_index = parent_index * 2 + 2

            if left_index < heap.size():
                self.assertLessEqual(
                    heap.items[parent_index], heap.items[left_index]
                )
            if right_index < heap.size():
                self.assertLessEqual(
                    heap.items[parent_index], heap.items[right_index]
                )


if __name__ == "__main__":
    unittest.main()
