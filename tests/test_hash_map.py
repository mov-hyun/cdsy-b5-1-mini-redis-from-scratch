"""Unit tests for the custom chaining hash map."""

import unittest

from mini_redis.hash_map import HashMap


class CollisionHashMap(HashMap):
    """Force every key into one bucket to exercise chaining."""

    def _hash(self, key):
        self._validate_key(key)
        return 1


class HashMapTests(unittest.TestCase):
    def test_capacity_must_be_a_positive_integer(self):
        with self.assertRaises(TypeError):
            HashMap(2.5)
        with self.assertRaises(TypeError):
            HashMap(True)
        with self.assertRaises(ValueError):
            HashMap(0)

    def test_put_get_contains_and_size(self):
        hash_map = HashMap()

        self.assertIsNone(hash_map.put("name", "Alice"))
        self.assertEqual(hash_map.get("name"), "Alice")
        self.assertTrue(hash_map.contains("name"))
        self.assertFalse(hash_map.contains("missing"))
        self.assertEqual(hash_map.size(), 1)

    def test_put_replaces_value_without_growing(self):
        hash_map = HashMap()
        hash_map.put("name", "Alice")

        old_value = hash_map.put("name", "Bob")

        self.assertEqual(old_value, "Alice")
        self.assertEqual(hash_map.get("name"), "Bob")
        self.assertEqual(hash_map.size(), 1)

    def test_contains_distinguishes_none_value_from_missing_key(self):
        hash_map = HashMap()
        hash_map.put("nullable", None)

        self.assertIsNone(hash_map.get("nullable"))
        self.assertTrue(hash_map.contains("nullable"))
        self.assertFalse(hash_map.contains("missing"))

    def test_remove_returns_value_and_clears_empty_bucket(self):
        hash_map = HashMap()
        hash_map.put("name", "Alice")
        bucket_index = hash_map._bucket_index("name")

        self.assertEqual(hash_map.remove("name"), "Alice")
        self.assertIsNone(hash_map.buckets[bucket_index])
        self.assertFalse(hash_map.contains("name"))
        self.assertEqual(hash_map.size(), 0)
        self.assertIsNone(hash_map.remove("name"))

    def test_chaining_handles_collisions_and_middle_removal(self):
        hash_map = CollisionHashMap()
        hash_map.put("first", 1)
        hash_map.put("middle", 2)
        hash_map.put("last", 3)

        self.assertEqual(hash_map.get("first"), 1)
        self.assertEqual(hash_map.get("middle"), 2)
        self.assertEqual(hash_map.get("last"), 3)
        self.assertEqual(hash_map.remove("middle"), 2)
        self.assertEqual(hash_map.get("first"), 1)
        self.assertIsNone(hash_map.get("middle"))
        self.assertEqual(hash_map.get("last"), 3)
        self.assertEqual(hash_map.size(), 2)

    def test_resize_occurs_only_after_load_factor_exceeds_threshold(self):
        hash_map = HashMap(capacity=4)
        hash_map.put("one", 1)
        hash_map.put("two", 2)
        hash_map.put("three", 3)

        self.assertEqual(hash_map.capacity, 4)

        hash_map.put("four", 4)

        self.assertEqual(hash_map.capacity, 8)
        self.assertEqual(hash_map.size(), 4)
        self.assertEqual(hash_map.get("one"), 1)
        self.assertEqual(hash_map.get("two"), 2)
        self.assertEqual(hash_map.get("three"), 3)
        self.assertEqual(hash_map.get("four"), 4)

    def test_collision_chain_survives_resize(self):
        hash_map = CollisionHashMap(capacity=2)

        for index in range(5):
            hash_map.put("key:{}".format(index), index)

        self.assertEqual(hash_map.capacity, 8)
        for index in range(5):
            self.assertEqual(hash_map.get("key:{}".format(index)), index)

    def test_keys_returns_every_key(self):
        hash_map = HashMap()
        expected_keys = ["user:1", "user:2", "한글키"]

        for key in expected_keys:
            hash_map.put(key, "value")

        self.assertEqual(sorted(hash_map.keys()), sorted(expected_keys))

    def test_hash_is_deterministic_and_supports_unicode(self):
        first_map = HashMap()
        second_map = HashMap(capacity=32)

        self.assertEqual(first_map._hash("사용자:1"), second_map._hash("사용자:1"))
        self.assertNotEqual(first_map._hash("사용자:1"), first_map._hash("사용자:2"))

    def test_only_string_keys_are_accepted(self):
        hash_map = HashMap()

        with self.assertRaises(TypeError):
            hash_map.put(123, "value")
        with self.assertRaises(TypeError):
            hash_map.get(123)
        with self.assertRaises(TypeError):
            hash_map.remove(123)
        with self.assertRaises(TypeError):
            hash_map.contains(123)


if __name__ == "__main__":
    unittest.main()
