import random
import heapq


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def clamp(val, minimum, maximum):
    return max(minimum, min(val, maximum))


def insert_into(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = []
    dictionary[key].append(value)


def insert_once(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = value
        

def pick_from_sorted_list(sorted_list):
    """Pick from a sorted list, with lower indices more likely to be picked."""
    if len(sorted_list) >= 3:
        # Pick from top three
        if random.random() < 0.6:
            choice = sorted_list[0]
        elif random.random() < 0.9:
            choice = sorted_list[1]
        else:
            choice = sorted_list[2]
    elif sorted_list:
        choice = list(sorted_list)[0]
    else:
        choice = None
    return choice