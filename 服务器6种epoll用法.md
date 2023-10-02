# 服务器6种epoll用法

## 前言：网络Socket

> 服务器socket是什么：**其一，这是一个文件；其二，它里面存的是所有客户端 Socket 文件的文件描述符**。

> 客户端连接服务器过程：
>
> 当**一个客户端连接到服务端的时候，操作系统就会创建一个客户端 Socket 的文件。**
>
> **然后操作系统将这个文件的文件描述符写入**服务端程序创建的服务端 Socket 文件中。
>
> **服务端 Socket 文件，是一个管道文件。**
>
> **如果读取这个文件的内容，就相当于从管道中取走了一个客户端文件描述符**。

![](C:\Users\8208191402\AppData\Roaming\Typora\typora-user-images\image-20220408140934950.png)

服务端 Socket 文件相当于一个客户端 Socket 的目录，线程可以通过 accept() 操作每次拿走一个客户端文件描述符。拿到客户端文件描述符，就相当于拿到了和客户端进行通信的接口。

### Socket总结

>Socket 首先是文件，存储的是数据。

> 对服务端而言，分成服务端 Socket 文件和客户端 Socket 文件。

> 服务端 Socket 文件存储的是客户端 Socket 文件描述符；
> 客户端 Socket 文件存储的是传输的数据。

> 读取客户端 Socket 文件，就是读取客户端发送来的数据；写入客户端文件，就是向客户端发送数据。对一个客户端而言， Socket 文件存储的是发送给服务端（或接收的）数据。

> 综上，Socket 首先是文件，在文件的基础上，**又封装了一段程序，这段程序提供了 API 负责最终的数据传输。**

### 第一种实现：扫描与监听

> 服务端程序，可以定期扫描服务端 Socket 文件的变更，来了解有哪些客户端想要连接进来。
>
> 如果在服务端 Socket 文件中读取到一个客户端的文件描述符，就可以将这个文件描述符实例化成一个 Socket 对象。

![在这里插入图片描述](https://img-blog.csdnimg.cn/2021070523575067.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3lhbmdzaGFuZ3dlaQ==,size_16,color_FFFFFF,t_70)

![在这里插入图片描述](https://img-blog.csdnimg.cn/20210705235819341.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3lhbmdzaGFuZ3dlaQ==,size_16,color_FFFFFF,t_70)

> 上述的过程，我们通过一个服务器线程就可以响应多个客户端的连接，也被称作**I/O 多路复用技术**。

### 第二种实现：响应式/事件驱动

> 当客户端很多时，轮询的开销很大，而且一个客户端的非正常请求和问题会严重影响其他客户端的正常请求。

#### 程序设计的角度分析

第一种叫命令式程序。一个处理程序主动遍历，比如遍历一个 Socket 集合看看有没有发生写入（有数据从网卡传过来），select 和 poll 都是**主动轮询机制**，需要拜訪每一個 FD；

命令式会让**负责处理线程/程序负载过重**，例如，在高并发场景下，上述讨论中循环遍历 Socket 集合的线程，会因为负担过重导致系统吞吐量下降。

第二种叫响应式程序。每一个参与者有着独立的思考方式，就好像拥有独立的人格，可以**自己针对不同的环境触发不同的行为**，例如epoll

响应式是让**某个观察者程序观察到 Socket 文件状态的变化**，当收到观察者变化信息时，**通知处理线程响应**。处理处理线程不再需要遍历 Socket 集合，而是等待观察程序的通知。

#### 观察者挑选

最合适的观察者：操作系统本身。

对 Socket 文件的读写都要经过操作系统，因此操作系统非常清楚每一个 Socket 文件的状态。

#### 模型实现的注意点：红黑树存储内容是客户端fd，目的是实现整数的高效插入查询

1.线程需要告诉中间的观察者要观察什么，也就是自己的行为，或者说在什么情况下才响应？比如具体到哪个 Socket 发生了什么事件？是读写还是其他的事件？这一步我们通常称为注册。

> 比如**线程对文件描述符 =123 的 Socket 文件读写**都感兴趣，会去中间观察者处注册。当 FD=123 的 Socket 发生读写时，中间观察者负责通知线程，这是一个响应式的模型。

2.中间的观察者需要实现一个高效的数据结构来存储客户端进程fd（通常是基于红黑树的二叉搜索树）。这是因为中间的观察者不仅仅是服务于某个线程，而是服务于很多的线程。**当一个 Socket 文件发生变化的时候**，中间观察者需要**立刻知道**，究竟**是哪个线程需要这个信息**，而不是将所有的线程都遍历一遍

> 比如当 FD=123 的 Socket 发生变化（读写等）时，能够快速地判断是哪个线程需要知道这个消息

综上所述，**中间观察者需要一个快速能插入（注册过程）、查询（通知过程）一个整数的数据结构，这个整数就是 Socket 的文件描述符**。

### 两种实现总结

**在服务端有两种 Socket 文件**，每个客户端接入之后会形成一个客户端的 Socket 文件，客户端 Socket 文件的文件描述符会存入服务端 Socket 文件。通过这种方式，一个线程可以通过读取服务端 Socket 文件中的内容拿到所有的客户端 Socket。**这样一个线程就可以负责响应所有客户端的 I/O，这个技术称为 I/O 多路复用。**

主动式的 I/O 多路复用，对负责 I/O 的线程压力过大，因此通常会设计一个高效的中间数据结构作为 I/O 事件的观察者和存储结构。线程通过订阅 I/O 事件被动响应，这就是响应式模型。

在 Socket 编程中，最适合提供这种中间数据结构的就是操作系统的内核，事实上 epoll 模型也是在操作系统的内核中提供了红黑树结构。

> select 是一个主动模型，需要服务线程自己注册一个集合存放所有的 Socket，然后发生 I/O 变化的时候遍历。
>
> 在 select 模型下，操作系统不知道哪个线程应该响应哪个事件，而是由线程自己去操作系统看有没有发生网络 I/O 事件，然后再遍历自己管理的所有 Socket，看看这些 Socket 有没有发生变化。

> poll 提供了更优质的编程接口，但是本质和 select 模型相同。因此千级并发以下的 I/O，你可以考虑 select 和 poll，但是如果出现更大的并发量，就需要用 epoll 模型。

> epoll 模型在操作系统内核中提供了**一个中间数据结构，这个中间数据结构会提供事件监听注册**，以及快速判断消息关联到哪个线程的能力（红黑树实现）。因此在高并发 I/O 下，可以考虑 epoll 模型，它的速度更快，开销更小。

## 正文：epoll的三个接口

> epoll_create()；
>
> epoll_ctl();
>
> epoll_wait(epfd，events，events. Length，-1);

> epfd：文件描述符，对应内核的一颗红黑树

### 大体框架和过程推导

#### 1.主线程负责events读写

```c++
if((fd==listenfd) && (events[i].events & EPOLLIN)){
    recv(events[i].data.fd,buffer,length,0);
    parser();
    send();
}
```

但是每个events文件描述符的处理耗时，想法：放到单独的线程里去

#### 2.主线程负责读取fd，子线程负责events读写

```c++
if((fd==listenfd) && (events[i].events & EPOLLIN)){
    push_to_other_thread(events[i].data.fd);
}
void* thread_cd(void* arg){
    int fd = *(int*) arg;
    recv(fd,buffer,length,0);
    parser();
    send();
}
```

可能会更糟，因为存在**多个进程共享fd**。

比如客户端发送第一组数据的时候，服务器主线程接收fd，抛给一个单独线程从主线程传来的fd去读数据，

而在发第二组数据的时候，对同一个文件的fd，主线程读取的文件fd，准备再开一个线程；前一个单开的线程可能会同时通过fd读数据，这会导致fd冲突的问题。

> LT:水平触发，语句出现一次就读一次
>
> ET:边沿触发，while读，读到-1为止

#### 3.确保服务器在客户端fd可用的时候才send回数据

```c++
if((fd==listenfd) && (events[i].events & EPOLLIN)){
    recv(events[i].data.fd,buffer,length,0);
    parser();
    epoll_ctl(epollfd,EPOLL_CTL_MOD,fd,EPOLL_OUT);
}//不由程序选择回传时间，由epoll负责
```

> 要send的数据放到哪里？下一次send的数据不在这里了，在epoll out事件里
>
> 引出epollfd结构体：fd+data

#### 4.服务器端通过connection，对客户端fd的存储

> 更泛化一些，用一个connection结构体表示一个连接的客户端的所有行为（回调函数）和数据

```c
struct connection{
    int fd;
    unsigned char[] wbuffer;
    int windex;
    unsigned char[] rbuffer;
    int rindex;
    unsigned char event_status;
    int (*send_cb)();
    int (*recv_cb)();
}
```

新的流程：客户端发来数据hello，服务器根据fd/sockfd找到对应的connection，传入行为event_status,根据行为调用适当的方法。

```c++
if((fd==listenfd) && (events[i].events & EPOLLIN)){
    connection = findConnection(events[i].data.fd);
    connection.recv(events[i].data.fd,buffer,length,0);
    connection.parser();
    epoll_ctl(epollfd,EPOLL_CTL_MOD,fd,EPOLL_OUT);
}//靠谱的单线程做法
```

也可能会有的问题：

1.epoll wait参数设置成-1的时候，会出现死循环、

2.如果epollwait返回的nready很大，在你for循环处理的时候，前面还没处理完，后面的fd关闭了，而没有能从你的events队列里删除，就会出现后面有空项。

### 多线程版本

#### 1. 1--M

> 一个accept线程，多个send和receive线程

```c++
int epfds[10];

lock_t lock;//防止惊群,确保sockfd同一时刻只出现在一个线程里
void* func(void* arg){
    int sockfd = *(int*)arg;
    pthread_t selfid = pthread_self();
    
   epfds[selfid%10] = epoll_create();
    
    while(true){
        if(lock == off){
            epoll_ctl(epfd,EPOLL_CTL_ADD,sockfd);
            lock = on;
            
            int nready = epoll_wait();//接受服务器分配过来的clientfd和对应事件，添加到events中
        	for(int i=0;i<nready;i++){
            	if(events[i].data.fd == sockfd){//连接
                	int clientfd = accept(sockfd,);
                	epoll_stl(epfd,clientfd);
            	}
        	}
        }else{
            //业务处理，传输数据
        }
        
    }
}
int main(){
    int id = 0;
    int sockfd = bind();
    listen(sockfd,backlog);
    epoll_ctl(e)
    for(int i=0;i<10;i++){
        pthread_create(,func,sockfd);
    }
    while(true){
        epoll();
        int clientfd = accept(sockfd);
        //这里就是主线程的瓶颈，
        //比如说服务器宕机重联，产生大量的reconnect，而所有的reconnect都是首先经过这里，然后才分配给子线程取单独处理业务
        //每秒接入量受到这里影响
        id%=10;
        id++;
        //非常简单的均衡负载方式
        epoll_ctl(epfds[id],EPOLL_CLT_ADD,clientfd,ev);
    }
}
```

> 使100000个io/socket/fd分布在多个线程的fd里面。
>
> 让IO处理得以并行，而不是数据读取之后，在业务处理上并行

> 主线程把sockfd传给子线程，子线程创建自己的epfd，把serverfd先放进去，然后等待主线程传递客户端fd，对自己负责的客户端进行连接服务 / 读写业务操作。

#### N--M

> 多个accept线程，多个send和receive线程

##### 短链接和长链接

>短链接：传输任务结束就中断连接
>
>长链接：长连接指建立SOCKET连接后不管是否使用都保持连接，直到一方关闭连接，多是客户端关闭连接。

![image-20220403133927414](C:\Users\8208191402\AppData\Roaming\Typora\typora-user-images\image-20220403133927414.png)

> 短连接例子：点击短信链接，跳转到短连接平台，短连接平台进行一次跳转到目标平台。
>
> 短链接每次数据接受处理不会有联系，这也是**HTTP协议无状态的原因之一**



对于长连接服务器（连接在一次读写之后保持），把while(1){accept}的部分拿出去单做一个线程没有太大的必要。

但是对于短连接（短信链接......），连接次数和send/recv次数是一样的，**重接入，轻处理**，接入次数非常多，可以采用N--M模式。

## 总结

### 单线程

1.recv/epoll，即recv之后直接用send函数传出去。

不可行，因为你没有检查对应的sockfd是否可写。

2.每次遇到一个fd请求就放到一个单独的线程里去处理，但是连接还是在主线程。

不可行，处理线程和主线程同时接受来自同一个sockfd的数据时，会出现共享文件描述符问题。

3.可行解：接收到数据之后，修改fd对应的时间状态为EPOLL_OUT，在下一次可写的时候，由epoll去写入，而不是我们手动控制

> 我们自己定义的业务connection里面的两个buffer是我们为了发送和接收数据业务创建的数组，不是TCP层面的发送和接受缓冲区。

### 多线程

1.主线程创建epoll，子线程公用一个epoll。

> 意义不大，因为epoll底层是通过红黑树存储客户端fd的，无论是查找还是添加都会有一个加锁的动作。

2.主线程创建listenfd，子线程自己创建epfd，把主线程的listenfd添加到自己的epfd里面。

> 惊群问题，只要通过保证listenfd只添加到一个子线程里面就行。

> *惊群问题不会影响业务逻辑，但会出现很多无效唤醒，一个新的连接会唤醒多个处理线程。*

也就是一个子线程负责处理链接，其他的负责处理读写。

3.主线程处理accept，多个子线程处理send/receive。

> 1）通过管道写入接受到的客户端fd，子线程从自己到主线程的管道里读出来。

> 2）强行负载均衡，通过数组下标取模，把主线程读到的客户端fd直接添加到对于子线程的epfd队列里。
>
> 简单，高效。主线程添加，子线程删除。

4.多进程：重复监听同一个端口，三级进程，主进程创建多个accept进程，accept创建各自的worker进程

![image-20220403141054606](C:\Users\8208191402\AppData\Roaming\Typora\typora-user-images\image-20220403141054606.png)
