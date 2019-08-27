# -*- coding: utf-8 -*-

from collections import deque

class BounceFilter(object):
    def __init__(self, size=10, discard_count=2):
        self.__size = size
        self.__discard_count = discard_count

        self.__data = deque(maxlen=size)

    @staticmethod
    def discard(data, discard_count):
        n = discard_count
        if len(data) <= n * 2:
            return data
        return data[n:-n]

    @staticmethod
    def extract_sorted_digits(data):
        d = list(n for n in data if n is not None)
        d.sort()
        return d

    def add(self, value):
        self.__data.extendleft([value])

    def get_all(self):
        return list(self.__data)

    def avg(self):
        digits = self.extract_sorted_digits(self.__data)
        values = self.discard(digits, self.__discard_count)
        if values:
            return sum(values) / len(values)
        return None
