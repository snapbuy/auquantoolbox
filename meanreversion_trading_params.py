from backtester.trading_system_parameters import TradingSystemParameters
from datetime import timedelta
from backtester.dataSource.google_data_source import GoogleStockDataSource
from backtester.dataSource.yahoo_data_source import YahooStockDataSource
from backtester.dataSource.nse_data_source import NSEStockDataSource
from backtester.executionSystem.simple_execution_system import SimpleExecutionSystem
from backtester.orderPlacer.backtesting_order_placer import BacktestingOrderPlacer
from backtester.trading_system import TradingSystem
from backtester.constants import *
from my_custom_feature import MyCustomFeature

start = '2010/01/01'
end = '2017/06/30'
assets = [ 'PNB', 'BANKBEES']#,'FEDERALBNK', 'ICICIBANK', 'CANBK', 'SBIN', 'YESBANK', 'KOTAKBANK', 
          #'BANKBARODA', 'HDFCBANK', 'AXISBANK', 'INDUSINDBK', 'NIFTYBEES']

class MyTradingParams(TradingSystemParameters):
    '''
    Returns an instance of class DataParser. Source of data for instruments
    '''

    def getDataParser(self):
        instrumentIds = assets
        startDateStr = start
        endDateStr = end
        return NSEStockDataSource(cachedFolderName='nseData',
                                     instrumentIds=instrumentIds,
                                     startDateStr=startDateStr,
                                     endDateStr=endDateStr)

    '''
    Returns a timedetla object to indicate frequency of updates to features
    Any updates within this frequncy to instruments do not trigger feature updates.
    Consequently any trading decisions that need to take place happen with the same
    frequency
    '''

    def getFrequencyOfFeatureUpdates(self):
        return timedelta(0, 30)  # minutes, seconds

    def getBenchmark(self):
        return 'BANKBEES'

    '''
    This is a way to use any custom features you might have made.
    Returns a dictionary where
    key: featureId to access this feature (Make sure this doesnt conflict with any of the pre defined feature Ids)
    value: Your custom Class which computes this feature. The class should be an instance of Feature
    Eg. if your custom class is MyCustomFeature, and you want to access this via featureId='my_custom_feature',
    you will import that class, and return this function as {'my_custom_feature': MyCustomFeature}
    '''

    def getCustomFeatures(self):
        return {'my_custom_feature': MyCustomFeature}

    '''
    Returns a dictionary with:
    key: string representing instrument type. Right now INSTRUMENT_TYPE_OPTION, INSTRUMENT_TYPE_STOCK, INSTRUMENT_TYPE_FUTURE
    value: Array of instrument feature config dictionaries
        feature config Dictionary has the following keys:
        featureId: a string representing the type of feature you want to use
        featureKey: {optional} a string representing the key you will use to access the value of this feature.
                    If not present, will just use featureId
        params: {optional} A dictionary with which contains other optional params if needed by the feature
    Example:
    positionConfigDict = {'featureId': 'position'}
    vwapConfigDict = {'featureKey': 'price',
                          'featureId': 'vwap'}
    movingAvg_30Dict = {'featureKey': 'mv_avg_30',
                          'featureId': 'moving_average',
                          'params': {'days': 30}}
    movingAvg_90Dict = {'featureKey': 'mv_avg_90',
                          'featureId': 'moving_average',
                          'params': {'days': 90}}
    return {INSTRUMENT_TYPE_FUTURE: [positionConfigDict, vwapConfigDict],
            INSTRUMENT_TYPE_STOCK: [positionConfigDict, movingAvg_30Dict, movingAvg_90Dict]}

    For each future instrument, you will have features keyed by position and price.
    For each stock instrument, you will have features keyed by position, mv_avg_30, mv_avg_90
    '''

    def getInstrumentFeatureConfigDicts(self):
        # ADD RELEVANT FEATURES HERE
        ma1Dict = {'featureKey': 'ma_90',
                   'featureId': 'moving_average',
                   'params': {'period': 90,
                              'featureName': 'close'}}
        ma2Dict = {'featureKey': 'ma_5',
                   'featureId': 'moving_average',
                   'params': {'period': 5,
                              'featureName': 'close'}}
        sdevDict = {'featureKey': 'sdev_90',
                    'featureId': 'moving_sdev',
                    'params': {'period': 90,
                               'featureName': 'close'}}
        momDict = {'featureKey': 'mom_90',
                   'featureId': 'momentum',
                   'params': {'period': 30,
                              'featureName': 'close'}}
        maRibbonDict = {'featureKey': 'ma_ribbon',
                   'featureId': 'ma_ribbon',
                   'params': {'startPeriod': 5,
                              'endPeriod': 100,
                              'numRibbons': 20,
                              'featureName': 'close'}}
        rsiDict = {'featureKey': 'rsi_30',
                   'featureId': 'rsi',
                   'params': {'period': 30,
                              'featureName': 'close'}}
        return {INSTRUMENT_TYPE_STOCK: [ma1Dict, ma2Dict, sdevDict,momDict, maRibbonDict, rsiDict]}

    '''
    Returns an array of market feature config dictionaries
        market feature config Dictionary has the following keys:
        featureId: a string representing the type of feature you want to use
        featureKey: a string representing the key you will use to access the value of this feature.this
        params: A dictionary with which contains other optional params if needed by the feature
    '''

    def getMarketFeatureConfigDicts(self):
        # ADD RELEVANT FEATURES HERE

        # customFeatureDict = {'featureKey': 'custom_mrkt_feature',
        #                      'featureId': 'my_custom_mrkt_feature',
        #                      'params': {'param1': 'value1'}}
        return []

    '''
    A function that returns your predicted value based on your heuristics.
    If you are just trading one asset like a stock, it could be the predicted value of the stock.
    If you are doing pair trading, the prediction could be the difference in the prices of the stocks.
    Arguments:
    time - When this prediction is being calculated
    currentMarketFeatures - Dictionary of market features which have been calculated at this update cycle.
    instrumentManager - Holder for all instruments and everything else if you need.
    '''

    def getPrediction(self, time, currentMarketFeatures, instrumentManager):
        instrumentIds = instrumentManager.getAllInstrumentsByInstrumentId()
        predictions = {}
        for ids in instrumentIds:
            instrument = instrumentManager.getInstrument(ids)

            if instrument is None:
                predictions[ids] = 0.5

            lookbackInstrumentFeatures = instrument.getDataDf().iloc[-1]
            # IMPLEMENT THIS
            if lookbackInstrumentFeatures['sdev_90'] != 0:
                z_score = (lookbackInstrumentFeatures['ma_5'] - lookbackInstrumentFeatures['ma_90']) / lookbackInstrumentFeatures['sdev_90']
            else:
                z_score = 0
            if z_score > 1:
                predictions[ids] = 0.2
            elif z_score < -1:
                predictions[ids] = 0.8
            elif (z_score > 0.5) or (z_score < -0.5) :
                predictions[ids] = 0.6
            else:
                predictions[ids] = 0.5

        return predictions

    '''
    Returns the type of execution system we want to use. Its an implementation of the class ExecutionSystem
    It converts prediction to intended positions for different instruments.
    '''

    def getExecutionSystem(self):
        return SimpleExecutionSystem(enter_threshold=0.7, 
                                     exit_threshold=0.55, 
                                     longLimit=10000, 
                                     shortLimit=10000,
                                     capitalUsageLimit = 0.10*self.getStartingCapital(), 
                                     lotSize=10)

    '''
    Returns the type of order placer we want to use. its an implementation of the class OrderPlacer.
    It helps place an order, and also read confirmations of orders being placed.
    For Backtesting, you can just use the BacktestingOrderPlacer, which places the order which you want, and automatically confirms it too.
    '''

    def getOrderPlacer(self):
        return BacktestingOrderPlacer()

    '''
    Returns the amount of lookback data you want for your calculations. The historical market features and instrument features are only
    stored upto this amount.
    This number is the number of times we have updated our features.
    '''

    def getLookbackSize(self):
        return 90


if __name__ == "__main__":
    tsParams = MyTradingParams()
    tradingSystem = TradingSystem(tsParams)
    tradingSystem.startTrading(onlyAnalyze=True, shouldPlot=False)
