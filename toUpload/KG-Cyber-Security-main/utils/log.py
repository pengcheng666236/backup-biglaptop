"""日志记录"""

# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler


class Logger(object):
    """日志记录
    """

    def __init__(self, logger):
        self.logger = logging.getLogger(logger)  # 设置root logger
        self.logger.handlers.clear()
        self.logger.setLevel(logging.DEBUG)
        # 使用FileHandler输出到文件
        fh = RotatingFileHandler('log/log.txt',
                                 mode='a',
                                 maxBytes=10 * 1024 * 1024,
                                 encoding='utf-8',
                                 backupCount=2,
                                 delay=0)
        fh.setLevel(logging.INFO)
        fh.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'))

        # 使用StreamHandler输出到屏幕
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # ch.setLevel(logging.DEBUG)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        # 添加两个Handler
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def getlog(self):
        return self.logger


logger = Logger(logger='graphy').getlog()
