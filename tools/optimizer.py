# @date 2018-08-07
# @author Frederic SCHERMA
# @license Copyright (c) 2018 Dream Overflow
# Siis standard implementation of the application (application main)

import sys
import logging
import traceback

from datetime import datetime

from instrument.instrument import Instrument
from common.utils import UTC, TIMEFRAME_FROM_STR_MAP, timeframe_to_str

from terminal.terminal import Terminal
from database.database import Database

import logging
logger = logging.getLogger('siis.tools.optimizer')

# candles from 1m to 1 month
GENERATED_TF = [60, 60*3, 60*5, 60*15, 60*30, 60*60, 60*60*2, 60*60*4, 60*60*24, 60*60*24*7, 60*60*24*30]
# GENERATED_TF = [60, 60*5, 60*15, 60*30, 60*60, 60*60*2, 60*60*4, 60*60*24, 60*60*24*7]

def format_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')


def format_delta(td):
    if td < 60.0:
        return "%.2f seconds" % timedelta

    if td < 60*60:
        m, r = divmod(td, 60)
        s = r

        return "%i minutes %i seconds" % (m, s)

    elif td < 60*60*24:
        h, r = divmod(td, 60*60)
        m, r = divmod(r, 60)
        s = r

        return "%i hours %i minutes %i seconds" % (h, m, s)

    else:
        d, r = divmod(td, 60*60*24)
        h, r = divmod(r, 60*60)
        m, r = divmod(r, 60)
        s = r

        return "%i days %i hours %i minutes %i seconds" % (d, h, m, s)


def check_ohlcs(broker_id, market_id, timeframe, from_date, to_date):
    last_ohlcs = {}

    ohlc_streamer = Database.inst().create_ohlc_streamer(broker_id, market_id, timeframe, from_date=from_date, to_date=to_date, buffer_size=100)
    timestamp = from_date.timestamp()
    to_timestamp = to_date.timestamp()
    progression = 0.0
    prev_update = timestamp
    count = 0
    total_count = 0

    progression_incr = (to_timestamp - timestamp) * 0.01

    tts = 0.0
    prev_tts = 0.0

    while not ohlc_streamer.finished():
        ohlcs = ohlc_streamer.next(timestamp + timeframe * 100)  # per 100

        count = len(ohlcs)
        total_count += len(ohlcs)

        for ohlc in ohlcs:
            tts = ohlc.timestamp

            if not prev_tts:
                prev_tts = tts

            gap_duration = tts - prev_tts

            if gap_duration > timeframe:
                date = format_datetime(timestamp)
                Terminal.inst().warning("Ohlc gap of %s on %s !" % (format_delta(gap_duration), date))

            if ohlc.bid_open <= 0.0:
                Terminal.inst().warning("Bid open price is lesser than 0 %s on %s !" % (ohlc.bid_open, date))
            if ohlc.bid_high <= 0.0:
                Terminal.inst().warning("Bid high price is lesser than 0 %s on %s !" % (ohlc.bid_high, date))
            if ohlc.bid_low <= 0.0:
                Terminal.inst().warning("Bid close price is lesser than 0 %s on %s !" % (ohlc.bid_low, date))
            if ohlc.bid_close <= 0.0:
                Terminal.inst().warning("Bid close price is lesser than 0 %s on %s !" % (ohlc.bid_close, date))

            if ohlc.ofr_open <= 0.0:
                Terminal.inst().warning("Ofr open price is lesser than 0 %s on %s !" % (ohlc.ofr_open, date))
            if ohlc.ofr_high <= 0.0:
                Terminal.inst().warning("Ofr high price is lesser than 0 %s on %s !" % (ohlc.ofr_high, date))
            if ohlc.ofr_low <= 0.0:
                Terminal.inst().warning("Ofr low price is lesser than 0 %s on %s !" % (ohlc.ofr_low, date))
            if ohlc.ofr_close <= 0.0:
                Terminal.inst().warning("Ofr close price is lesser than 0 %s on %s !" % (ohlc.ofr_close, date))

            if ohlc.volume <= 0.0:
                Terminal.inst().warning("Volume quantity is lesser than 0 %s on %s !" % (ohlc.volume, date))

            prev_tts = tts

        if timestamp - prev_update >= progression_incr:
            progression += 1
            
            Terminal.inst().info("%i%% on %s, %s ticks/trades for 1 minute, current total of %s..." % (progression, format_datetime(timestamp), count, total_count))
            
            prev_update = timestamp
            count = 0

        if timestamp > to_timestamp:
            break

        timestamp += timeframe * 100  # per 100

    if progression < 100:
        Terminal.inst().info("100%% on %s, %s ticks/trades for 1 minute, current total of %s..." % (format_datetime(timestamp), count, total_count))


def check_ticks(broker_id, market_id, from_date, to_date):
    last_ticks = []

    tick_streamer = Database.inst().create_tick_streamer(broker_id, market_id, from_date=from_date, to_date=to_date)
    timestamp = from_date.timestamp()
    to_timestamp = to_date.timestamp()
    progression = 0.0
    prev_update = timestamp
    count = 0
    total_count = 0

    progression_incr = (to_timestamp - timestamp) * 0.01

    tts = 0.0
    prev_tts = 0.0

    while not tick_streamer.finished():
        ticks = tick_streamer.next(timestamp + Instrument.TF_1M)

        count = len(ticks)
        total_count += len(ticks)

        for data in ticks:
            tts = float(data[0]) * 0.001
            bid = float(data[1])
            ofr = float(data[2])
            vol = float(data[3])

            if not prev_tts:
                prev_tts = tts

            gap_duration = tts - prev_tts

            if gap_duration > 60.0:
                date = format_datetime(timestamp)
                Terminal.inst().warning("Tick gap of %s on %s !" % (format_delta(gap_duration), date))

            if bid <= 0.0:
                Terminal.inst().warning("Bid price is lesser than 0 %s on %s !" % (bid, date))
            if ofr <= 0.0:
                Terminal.inst().warning("Ofr price is lesser than 0 %s on %s !" % (ofr, date))

            if vol <= 0.0:
                Terminal.inst().warning("Volume quantity is lesser than 0 %s on %s !" % (vol, date))

            prev_tts = tts

        if timestamp - prev_update >= progression_incr:
            progression += 1
            
            Terminal.inst().info("%i%% on %s, %s ticks/trades for 1 minute, current total of %s..." % (progression, format_datetime(timestamp), count, total_count))
            
            prev_update = timestamp
            count = 0

        if timestamp > to_timestamp:
            break

        timestamp += Instrument.TF_1M  # by step of 1m

    if progression < 100:
        Terminal.inst().info("100%% on %s, %s ticks/trades for 1 minute, current total of %s..." % (format_datetime(timestamp), count, total_count))


def do_optimizer(options):
    Terminal.inst().info("Starting SIIS optimizer...")
    Terminal.inst().flush()

    # database manager
    Database.create(options)
    Database.inst().setup(options)

    broker_id = options['broker']
    market_id = options['market']

    timeframe = None

    from_date = options.get('from')
    to_date = options.get('to')

    if not to_date:
        today = datetime.now().astimezone(UTC())

        if timeframe == Instrument.TF_MONTH:
            to_date = today + timedelta(months=1)
        else:
            to_date = today + timedelta(seconds=timeframe)

        to_date = to_date.replace(microsecond=0)

    if not options.get('timeframe'):
        timeframe = None
    else:
        if options['timeframe'] in TIMEFRAME_FROM_STR_MAP:
            timeframe = TIMEFRAME_FROM_STR_MAP[options['timeframe']]
        else:
            try:
                timeframe = int(options['timeframe'])
            except:
                pass

    try:
        # checking data integrity, gap...
        if timeframe is None:
            for market in options['market'].split(','):
                if market.startswith('!') or market.startswith('*'):
                    continue

                for tf in GENERATED_TF:
                    Terminal.inst().info("Verifying %s OHLC %s..." % (market, timeframe_to_str(tf)))

                    check_ohlcs(options['broker'], market, tf, from_date, to_date)

        elif timeframe == Instrument.TF_TICK:
            for market in options['market'].split(','):
                if market.startswith('!') or market.startswith('*'):
                    continue

                Terminal.inst().info("Verifying %s ticks/trades..." % (market,))

                check_ticks(options['broker'], market, from_date, to_date)

        elif timeframe > 0:
            # particular ohlc
            for market in options['market'].split(','):
                if market.startswith('!') or market.startswith('*'):
                    continue

                Terminal.inst().info("Verifying %s OHLC %s..." % (market, timeframe_to_str(timeframe)))

                check_ohlcs(options['broker'], market, timeframe, from_date, to_date)
    except KeyboardInterrupt:
        pass
    finally:
        pass

    Terminal.inst().info("Flushing database...")
    Terminal.inst().flush() 

    Database.terminate()

    Terminal.inst().info("Optimization done!")
    Terminal.inst().flush()

    Terminal.terminate()
    sys.exit(0)
