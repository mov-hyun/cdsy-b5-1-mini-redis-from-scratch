"""Channel-based publish/subscribe with per-subscriber message queues."""

from .hash_map import HashMap
from .linked_list import DoublyLinkedList


class Subscriber:
    """A client that buffers delivered messages in a FIFO queue."""

    def __init__(self):
        self.inbox = DoublyLinkedList()
        self.channel_count = 0

    def drain(self):
        """Pop every buffered (channel, message) pair in arrival order."""
        messages = []
        while len(self.inbox):
            messages.append(self.inbox.remove_front().data)
        return messages


class PubSub:
    """Map each channel to the linked list of its subscribers."""

    def __init__(self):
        self.channels = HashMap()

    def subscribe(self, channel, subscriber):
        """Register subscriber on channel; return its total channel count."""
        members = self.channels.get(channel)
        if members is None:
            members = DoublyLinkedList()
            self.channels.put(channel, members)
        if not self._contains(members, subscriber):
            members.insert_back(subscriber)
            subscriber.channel_count += 1
        return subscriber.channel_count

    def publish(self, channel, message):
        """Enqueue message for every subscriber; return how many received it."""
        members = self.channels.get(channel)
        if members is None:
            return 0
        node = members.head
        while node is not None:
            node.data.inbox.insert_back((channel, message))
            node = node.next
        return len(members)

    @staticmethod
    def _contains(members, subscriber):
        # ponytail: O(subscribers) duplicate check, fine for a CLI demo.
        node = members.head
        while node is not None:
            if node.data is subscriber:
                return True
            node = node.next
        return False
