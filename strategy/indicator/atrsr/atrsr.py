# @date 2019-10-18
# @author Frederic SCHERMA
# @license Copyright (c) 2019 Dream Overflow
# Average True Range support and resistance indicator

from strategy.indicator.indicator import Indicator
from strategy.indicator.utils import MM_n, down_sample
from talib import ATR as ta_ATR, EMA as ta_EMA, MAX as ta_MAX, MIN as ta_MIN, SMA as ta_SMA

import numpy as np

import logging
logger = logging.getLogger('siis.strategy.indicator')


class ATRSRIndicator(Indicator):
    """
    Average True Range Support and Resistance indicator.
    """

    __slots__ = '_length', '_coeff', '_length_MA', '_down', '_up', '_both', '_max_history', '_tup', '_tdn', '_last_atr', '_last_up', '_last_dn'

    @classmethod
    def indicator_type(cls):
        return Indicator.TYPE_TREND

    @classmethod
    def indicator_class(cls):
        return Indicator.CLS_OSCILLATOR

    def __init__(self, timeframe, length=14, coeff=2, length_MA=7, max_history=100):
        super().__init__("atrsr", timeframe)

        self._compute_at_close = True  # only at close

        self._length = length   # MA periods number
        self._coeff = coeff
        self._length_MA = length_MA

        self._max_history = max_history

        self._down = []
        self._up = []
        self._both = []

        self._tup = np.array([])
        self._tdn = np.array([])

        self._last_atr = 0.0
        self._last_up = 0.0
        self._last_dn = 0.0

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, length):
        self._length = length

    @property
    def down(self):
        return self._down

    @property
    def up(self):
        return self._up

    @property
    def last_up(self):
        """Valid only if the last computation generate a new up else 0.0"""
        return self._last_up

    @property
    def last_down(self):
        """Valid only if the last computation generate a new down else 0.0"""
        return self._last_dn

    def search_up(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in reversed(self._up):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in reversed(self._up):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def search_sorted_up(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in sorted(self._up):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in sorted(self._up, reverse=True):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def search_down(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in reversed(self._down):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in reversed(self._down):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def search_sorted_down(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in sorted(self._down):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in sorted(self._down, reverse=True):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def search_both(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in reversed(self._both):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in reversed(self._both):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def search_sorted_both(self, direction, last_price, depth=1, epsilon=0.0):
        n = 0
        stop_loss = last_price

        if direction > 0:
            for x in sorted(self._both):
                if x > stop_loss + epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        elif direction < 0:
            for x in sorted(self._both, reverse=True):
                if x < stop_loss - epsilon:
                    stop_loss = x
                    n += 1

                    if n >= depth:
                        return stop_loss

        return 0.0

    def compute(self, timestamp, timestamps, high, low, close):
        size = len(close)

        basis = ta_SMA(close, self._length)
        atrs = ta_ATR(high, low, close, timeperiod=self._length)

        dev = atrs * self._coeff
        upper = basis + dev
        lower = basis - dev

        try:
            bbr = (close - lower) / (upper - lower)
        except RuntimeWarning:
            logger.warning("bbr = (close - lower) / (upper - lower) divided by zero")
            logger.warning(close)
            logger.warning(lower)
            logger.warning(upper)
            logger.warning(lower)
            logger.warning(atrs)

        bbe = ta_EMA(bbr, self._length_MA)

        if len(self._tup) != size:
            self._tup = np.zeros(size)
            self._tdn = np.zeros(size)

        for i in range(2, size):
            if bbe[i-1] > bbe[i] and bbe[i-2] < bbe[i-1]:
                self._tup[i] = bbe[i]
            else:
                self._tup[i] = np.NaN

        for i in range(2, size):
            if bbe[i-1] < bbe[i] and bbe[i-2] < bbe[i-1]:
                self._tdn[i] = bbe[i]
            else:
                self._tdn[i] = np.NaN

        highest = ta_MAX(high, 3)
        lowest = ta_MIN(low, 3)

        last_up = 0.0
        last_dn = 0.0

        for i in range(0, size):
            if not np.isnan(self._tup[i]):
                last_up = self._tup[i] = highest[i]
            else:
                self._tup[i] = last_up

            if not np.isnan(self._tdn[i]):
                last_dn = self._tdn[i] = lowest[i]
            else:
                self._tdn[i] = last_dn

        # compact timeserie
        delta = min(int((timestamp - self._last_timestamp) / self._timeframe), len(timestamps))

        # base index
        num = len(timestamps)

        # signal for a new dn/up
        self._last_dn = 0.0
        self._last_up = 0.0

        for b in range(num-delta, num):
            if timestamps[b] > self._last_timestamp:
                if b > 0:
                    last_up = self._tup[b-1]
                    last_dn = self._tdn[b-1]
                else:
                    last_up = 0.0
                    last_dn = 0.0

                if not np.isnan(self._tup[b]) and self._tup[b] != last_up:
                    last_up = self._tup[b]

                    self._up.append(last_up)
                    self._both.append(last_up)

                    # retains the last for signal
                    self._last_up = last_up

                    if len(self._up) > self._max_history:
                        self._up.pop(0)

                    if len(self._both) > 2*self._max_history:
                        self._both.pop(0)

                if not np.isnan(self._tdn[b]) and self._tdn[b] != last_dn:
                    last_dn = self._tdn[b]

                    self._down.append(last_dn)
                    self._both.append(last_dn)

                    # retains the last for signal
                    self._last_dn = last_dn

                    if len(self._down) > self._max_history:
                        self._down.pop(0)

                    if len(self._both) > 2*self._max_history:
                        self._both.pop(0)

        # if self.timeframe == 60*60*24:
        #     logger.info("%s %s" % (self._tup, self._tdn))
        #     logger.info("%s %s" % (self._up, self._down))
        # if self.timeframe == 60*60*24:
        #     logger.info("%s" % (self._both))

        if len(atrs):
            # retains last ATR value
            self._last_atr = atrs[-1]

        self._last_timestamp = timestamp

        return self._up, self._down

    def loads(self, data):
        pass

    def dumps(self):
        return {}
