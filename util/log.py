import os
import logging
from logging import handlers
import time

_logDict = {}

def makeLogger(moduleName):
    date = time.strftime('%Y%m%d%H', time.localtime(time.time()))
    fileName = moduleName + '_' + date + '.txt'
    #创建日志级别
    logger = logging.getLogger(moduleName)
    logger.setLevel(logging.INFO)

    #定义日志格式
    formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(filename)s|%(funcName)s|%(lineno)d|%(message)s')

    # 
    th = handlers.TimedRotatingFileHandler(fileName, when='H', encoding='utf-8')
    th.setFormatter(formatter)

    #添加到日志记录器中
    logger.addHandler(th)
    logger.info("init")

    _logDict.update({moduleName: {'logFileName':moduleName, 'log':logger}})


def getLogger(moduleName):
    if not _logDict.__contains__(moduleName):
        makeLogger(moduleName)

    return _logDict[moduleName]['log']


if __name__ == "__main__":
    log = getLogger("default")
    log.info("test")


    log = getLogger("ddd")
    log.info("test")

    log = getLogger("default")
    log.info("test")


    log = getLogger("ddd")
    log.info("test")
