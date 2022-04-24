import os
from pathlib import Path
import logging
from logging import handlers
import time

_logDict = {}
logDir = os.path.abspath(".") + '/log/'
log0 = Path("./log/")
if not log0.exists():
    os.mkdir(log0)


def makeLogger(fileName):
    #创建日志级别
    logger = logging.getLogger(fileName)
    logger.setLevel(logging.INFO)

    #定义日志格式
    formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d|%(message)s')

    # 
    th = handlers.TimedRotatingFileHandler(logDir+fileName+".txt", when='H', encoding='utf-8')
    th.setFormatter(formatter)

    #添加到日志记录器中
    logger.addHandler(th)
    logger.info("init")

    _logDict.update({fileName: {'logFileName':fileName, 'log':logger}})


def getLogger(moduleName):
    date = time.strftime('%Y%m%d%H', time.localtime(time.time()))
    fileName = moduleName + '_' + date
    if not _logDict.__contains__(fileName):
        makeLogger(fileName)

    return _logDict[fileName]['log']