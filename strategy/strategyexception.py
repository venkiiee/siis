# @date 2018-09-08
# @author Frederic SCHERMA
# @license Copyright (c) 2019 Dream Overflow
# Strategy exceptions classes

from app.appexception import ServiceException


class StrategyServiceException(ServiceException):

    def __init__(self, message):
        super().__init__("strategy", message)

    def __str__(self):
        return 'StrategyServiceException (%s) : %s' % (self.service_name, self.message)


class StrategyException(StrategyServiceException):

    def __init__(self, strategy_name, appliance_identifier, message):
        super().__init__(message)

        self.strategy_name = strategy_name
        self.appliance_identifier = appliance_identifier

    def __str__(self):
        return 'StrategyException (%s:%s) : %s' % (
            self.strategy_name, self.appliance_identifier, self.message)


class StrategyTraderException(StrategyException):

    def __init__(self, strategy_name, appliance_identifier, instrument_id, message):
        super().__init__(strategy_name, appliance_identifier, message)

        self.instrument_id = instrument_id

    def __str__(self):
        return 'StrategyTraderException (%s:%s:%s) : %s' % (
            self.strategy_name, self.appliance_identifier, self.instrument_id, self.message)


class StrategySubTraderException(StrategyTraderException):

    def __init__(self, name, appliance_identifier, instrument_id, sub_id, message):
        super().__init__(strategy_name, appliance_identifier, instrument_id, message)

        self.instrument_id = instrument_id

    def __str__(self):
        return 'StrategySubTraderException (%s:%s:%s:%s) : %s' % (
            self.strategy_name, self.appliance_identifier, self.instrument_id, self.instrument_id, self.message)
