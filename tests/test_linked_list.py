"""Unit tests for the custom doubly linked list."""

import unittest

from mini_redis.linked_list import DoublyLinkedList, LinkedListNode


class DoublyLinkedListTests(unittest.TestCase):
    def test_empty_list_has_no_removable_node(self):
        linked_list = DoublyLinkedList()

        self.assertIsNone(linked_list.remove_front())
        self.assertIsNone(linked_list.remove_back())
        self.assertEqual(len(linked_list), 0)

    def test_insert_front_links_nodes_in_both_directions(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_front("first")
        second = linked_list.insert_front("second")

        self.assertIs(linked_list.head, second)
        self.assertIs(linked_list.tail, first)
        self.assertIs(second.next, first)
        self.assertIs(first.prev, second)
        self.assertIsNone(second.prev)
        self.assertIsNone(first.next)
        self.assertEqual(len(linked_list), 2)

    def test_insert_back_links_nodes_in_both_directions(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        second = linked_list.insert_back("second")

        self.assertIs(linked_list.head, first)
        self.assertIs(linked_list.tail, second)
        self.assertIs(first.next, second)
        self.assertIs(second.prev, first)
        self.assertEqual(len(linked_list), 2)

    def test_remove_front_and_back_update_boundaries(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        middle = linked_list.insert_back("middle")
        last = linked_list.insert_back("last")

        self.assertIs(linked_list.remove_front(), first)
        self.assertIs(linked_list.head, middle)
        self.assertIsNone(middle.prev)
        self.assertIs(linked_list.remove_back(), last)
        self.assertIs(linked_list.tail, middle)
        self.assertIsNone(middle.next)
        self.assertEqual(len(linked_list), 1)

    def test_remove_node_unlinks_middle_node(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        middle = linked_list.insert_back("middle")
        last = linked_list.insert_back("last")

        removed = linked_list.remove_node(middle)

        self.assertIs(removed, middle)
        self.assertIs(first.next, last)
        self.assertIs(last.prev, first)
        self.assertIsNone(middle.prev)
        self.assertIsNone(middle.next)
        self.assertEqual(len(linked_list), 2)

    def test_removing_only_node_restores_empty_state(self):
        linked_list = DoublyLinkedList()
        only_node = linked_list.insert_front("only")

        self.assertIs(linked_list.remove_node(only_node), only_node)
        self.assertIsNone(linked_list.head)
        self.assertIsNone(linked_list.tail)
        self.assertEqual(len(linked_list), 0)

    def test_move_to_front_handles_tail_middle_and_head(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        middle = linked_list.insert_back("middle")
        last = linked_list.insert_back("last")

        self.assertIs(linked_list.move_to_front(last), last)
        self.assertIs(linked_list.head, last)
        self.assertIs(linked_list.tail, middle)
        self.assertIs(last.next, first)
        self.assertIs(first.next, middle)
        self.assertIs(middle.prev, first)

        self.assertIs(linked_list.move_to_front(first), first)
        self.assertIs(linked_list.head, first)
        self.assertIs(first.next, last)
        self.assertIs(last.prev, first)
        self.assertIs(linked_list.move_to_front(first), first)
        self.assertEqual(len(linked_list), 3)

    def test_foreign_or_already_removed_node_is_rejected(self):
        linked_list = DoublyLinkedList()
        node = linked_list.insert_front("owned")
        foreign_node = LinkedListNode("foreign")

        self.assertIsNone(linked_list.remove_node(foreign_node))
        self.assertIsNone(linked_list.move_to_front(foreign_node))
        self.assertIs(linked_list.remove_node(node), node)
        self.assertIsNone(linked_list.remove_node(node))
        self.assertEqual(len(linked_list), 0)


if __name__ == "__main__":
    unittest.main()
