@[TOC](skynet网络模块)

# 简介

skynet：c+lua实现的，actor并发编程模型

erlang：语言层面实现的actor并发编程模型

actor：抽象的，用户空间的抽象进程

![image-20220516215905916](C:\Users\8208191402\AppData\Roaming\Typora\typora-user-images\image-20220516215905916.png)

上图就是一个内核进程抽象出的多个用户进程，消息通信方式。

## actor组成部分

- 隔离的运行环境：lua虚拟机
- 通信中间件：消息队列
- 运行actor的工具：**回调函数**，执行actor

























# Reactor网络模块封装



# 数据如何到达Actor

# 网络操作的同步非阻塞实现

