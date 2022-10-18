"""装饰器记录函数运行时长"""

# -*- coding: utf-8 -*-

import functools
import time
from utils.log import logger


def timer(fn):
    """装饰器记录函数运行时长
    """
    @functools.wraps(fn)
    def wrapper(*args, **kw):
        s_time = time.time()  # 记录开始时间
        f = fn(*args, **kw)  # 开始执行函数
        e_time = time.time()  # 记录结束时间
        logger.info('%s 运行 %.4fs' % (fn.__name__, e_time - s_time))
        return f
    return wrapper
