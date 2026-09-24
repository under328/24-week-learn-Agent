# Day 33 — 后端常见面试题速览

## 引言:为什么 Agent 工程师必须懂后端?

很多从算法或移动端转 Agent 方向的同学会有一个误区:"我做 LLM 应用,主要调 Prompt 和模型,后端是后端工程师的事。"

这个想法在 Demo 阶段成立,但**一旦要把 Agent 做成线上产品**,后端能力就是分水岭:

- **Agent 服务化**:Agent 不是一次性调用的函数,而是有状态、会持续运行的"长任务"。如何托管 Agent 的运行时?如何处理超时、重试、断点续跑?
- **API 设计**:LLM 推理慢(秒级),传统 REST 同步接口会让用户干等。需要 SSE/WebSocket 流式输出、异步任务回调、长轮询等设计。
- **数据库**:Agent 的会话历史、工具调用记录、用户画像都要持久化。向量库 + 关系库 + 缓存如何分工?
- **消息队列**:Agent 编排往往涉及多步、多工具、多 Agent 协作,用 MQ 解耦、削峰、重试是标配。
- **高并发**:一旦 Agent 接入 C 端,LLM 推理本身就是瓶颈,必须用缓存(语义缓存)、限流、排队、降级来保护系统。

华为背景的同学在面试时,面试官会**默认你懂后端**(因为华为内部很多自研中间件),所以这部分不能丢分。本 Day 不从零讲起,而是把高频考点浓缩成 10 道面试题,帮你快速过一遍。

### 今日学习目标

1. 掌握操作系统、网络、数据库、Redis、并发、MQ、微服务 7 大板块的高频考点
2. 能用一段话讲清楚每个核心概念(面试时 1-2 分钟回答)
3. 能手写一个简化版线程池(代码题必考)
4. 能画出 Agent 服务后端架构图(系统设计题,与 Agent 结合)
5. 识别 10 个常见易错点,避免"会但答错"

---

## 今日知识图谱

```
后端知识体系
├── 操作系统 (OS)
│   ├── 进程 vs 线程 vs 协程
│   ├── 进程间通信 (管道/消息队列/共享内存/信号量/Socket)
│   ├── 虚拟内存 (页表/TLB/缺页中断)
│   ├── 死锁 (四条件 / 预防 / 避免 / 检测)
│   └── IO 模型 (阻塞 / 非阻塞 / IO多路复用 / 信号驱动 / 异步IO)
│       └── epoll (select/poll 对比, 边沿触发 vs 水平触发)
│
├── 计算机网络
│   ├── TCP/UDP
│   │   ├── TCP 可靠性 (序号/确认/重传/流量控制/拥塞控制)
│   │   ├── 三次握手 / 四次挥手 (TIME_WAIT / 半连接队列)
│   │   └── 拥塞控制 (慢启动 / 拥塞避免 / 快重传 / 快恢复)
│   ├── HTTP/HTTPS (HTTP1.1 / 2.0 / 3.0, TLS 握手)
│   └── DNS 解析流程 (递归 / 迭代, 浏览器缓存 → ... → 根域名)
│
├── 数据库 (MySQL)
│   ├── 索引 (B+树 / 聚簇索引 / 覆盖索引 / 最左前缀 / 索引下推)
│   ├── 事务 (ACID / 隔离级别 / MVCC / ReadView)
│   ├── 锁 (行锁 / 表锁 / 间隙锁 / Next-Key Lock / 意向锁)
│   ├── 日志 (redo / undo / binlog / 两阶段提交)
│   └── SQL 优化 (explain / 回表 / 慢查询)
│
├── Redis
│   ├── 数据结构 (String/List/Hash/Set/Zset + 底层 SDS/跳表/压缩列表)
│   ├── 持久化 (RDB / AOF / 混合持久化)
│   ├── 缓存问题 (穿透 / 击穿 / 雪崩)
│   ├── 分布式锁 (SETNX / Redisson / RedLock)
│   ├── 过期策略 (惰性 + 定期) 与淘汰策略 (LRU/LFU/random)
│   └── 高可用 (主从 / 哨兵 / Cluster)
│
├── 并发编程
│   ├── 线程池 (7 参数 / 工作流程 / 4 拒绝策略 / 合理配置)
│   ├── 锁 (synchronized / ReentrantLock / 读写锁)
│   ├── volatile (可见性 / 禁止重排序 / 不保证原子性)
│   ├── CAS 与 ABA (AtomicXxx / 版本号)
│   ├── AQS (state / CLH 队列 / 独占 vs 共享)
│   └── 并发容器 (ConcurrentHashMap / CopyOnWrite / BlockingQueue)
│
├── 消息队列 (MQ)
│   ├── 选型 (Kafka 吞吐 / RabbitMQ 路由 / RocketMQ 事务)
│   ├── 可靠性 (生产端确认 / 持久化 / 消费端 ack)
│   ├── 有序性 (单分区 / 单队列)
│   ├── 重复消费 (幂等)
│   └── 堆积 (扩容 / 死信 / 跳过)
│
└── 微服务
    ├── 服务治理 (注册发现 / 负载均衡 / 熔断降级 / 限流)
    ├── 链路追踪 (TraceId / Span / 采样)
    ├── API 网关 (鉴权 / 限流 / 路由 / 协议转换)
    ├── 配置中心 (热更新 / 灰度)
    └── 分布式事务 (2PC / 3PC / TCC / Saga / 本地消息表 / 最大努力通知)
```

---

## 面试题(共 10 道)

> **使用建议**:先看题目自己默答一遍(可以用费曼技巧讲出来),再展开 `<details>` 对照参考答案。能讲出来 ≠ 答得对。

### Q1 操作系统核心:进程/线程/IO 模型/死锁

**题目**:请讲讲进程和线程的区别、进程间通信方式、虚拟内存、死锁的条件与预防,以及 IO 模型(尤其是 epoll)。

<details>
<summary>展开参考答案</summary>

#### 1. 进程 vs 线程 vs 协程

| 维度 | 进程 | 线程 | 协程 |
|------|------|------|------|
| 资源分配 | 独立地址空间 | 共享进程内存 | 共享线程栈 |
| 切换成本 | 高(切换页表/TLB 失效) | 中(切换寄存器/栈) | 低(用户态切换) |
| 通信 | IPC(管道/共享内存等) | 直接读写共享变量 | 同线程内直接通信 |
| 并发数 | 几十~几百 | 几百~几千 | 几万~几十万 |

**核心记忆点**:进程是资源分配的最小单位,线程是 CPU 调度的最小单位。

#### 2. 进程间通信 (IPC)

- **管道 (pipe)**:半双工,父子进程间;**命名管道 (FIFO)**:任意进程间。
- **消息队列**:内核中的链表,有格式。
- **共享内存**:**最快**的 IPC,因为不涉及内核态拷贝;需配信号量同步。
- **信号量**:同步互斥,不是传数据。
- **信号**:异步通知(如 SIGKILL)。
- **Socket**:跨机器通信。

#### 3. 虚拟内存

每个进程有独立虚拟地址空间,通过**页表**映射到物理内存。

- **TLB**:页表的硬件缓存,加速地址翻译。
- **缺页中断**:访问的页不在物理内存,从磁盘换入。
- **作用**:隔离进程、内存扩展(换出)、懒加载、写时复制(fork)。

#### 4. 死锁

**四个必要条件**(缺一不可):
1. 互斥
2. 占有并等待
3. 不可剥夺
4. 循环等待

**处理策略**:
- **预防**:破坏四条件之一(如所有资源按序申请,破坏循环等待)。
- **避免**:银行家算法,分配前判断是否进入不安全状态。
- **检测与恢复**:资源分配图检测环,kill 进程恢复。
- **忽略**:大多数通用 OS(如 Linux)忽略,靠重启。

#### 5. IO 模型

五大 IO 模型(以 read 为例):
- **阻塞 IO**:调用阻塞直到数据就绪并拷贝完成。默认。
- **非阻塞 IO**:数据未就绪立即返回 EAGAIN,需轮询。
- **IO 多路复用**:select/poll/epoll,一个线程监听多个 fd。
- **信号驱动 IO**:内核就绪后发 SIGIO,应用再读。
- **异步 IO (AIO)**:内核完成拷贝后通知应用。真正异步。

**epoll vs select/poll**:

| 项 | select | poll | epoll |
|----|--------|------|-------|
| 文件描述符上限 | 1024 (FD_SETSIZE) | 无上限 | 无上限 |
| 时间复杂度 | O(n) 遍历 | O(n) 遍历 | O(1),回调机制 |
| fd 拷贝 | 每次调用全量拷贝 | 每次全量拷贝 | 只在 epoll_ctl 时拷贝一次 |
| 工作方式 | 水平触发 | 水平触发 | 水平 + 边沿 |

**水平触发 (LT)**:只要 fd 有数据可读,一直通知(默认)。**边沿触发 (ET)**:只在状态变化时通知一次,必须一次性读完(配合非阻塞 IO)。

**epoll 底层**:红黑树存监听 fd,就绪 fd 通过双向链表回调加入就绪队列。

</details>

---

### Q2 计算机网络深入:TCP/UDP/三次握手/DNS

**题目**:TCP 和 UDP 的区别?TCP 如何保证可靠性?三次握手和四次挥手为什么不能少一次?DNS 解析流程?

<details>
<summary>展开参考答案</summary>

#### 1. TCP vs UDP

| 维度 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接(三次握手) | 无连接 |
| 可靠性 | 可靠(序号/确认/重传) | 不可靠 |
| 顺序 | 有序 | 无序 |
| 速度 | 慢 | 快 |
| 头部 | 20 字节 | 8 字节 |
| 拥塞控制 | 有 | 无 |
| 应用 | HTTP/SSH/FTP | DNS/视频/游戏/QUIC |

#### 2. TCP 可靠性机制

- **序号与确认**:每个字节有序号,接收方累计确认。
- **重传**:超时重传(RTO,RTT 加权平均)+ 快速重传(连续 3 个重复 ACK)。
- **流量控制**:滑动窗口,接收方通过 ACK 通告窗口大小,防止淹没接收方。
- **拥塞控制**:
  - **慢启动**:cwnd 从 1 指数增长到 ssthresh。
  - **拥塞避免**:超过 ssthresh 后线性增长。
  - **快重传**:3 个重复 ACK 立即重传,不等超时。
  - **快恢复**:ssthresh = cwnd/2,cwnd = ssthresh,线性增长(不回到 1)。

#### 3. 三次握手

```
Client -> Server: SYN, seq=x           (SYN_SENT)
Server -> Client: SYN+ACK, seq=y, ack=x+1  (SYN_RCVD)
Client -> Server: ACK, ack=y+1         (ESTABLISHED)
```

**为什么不是两次?**
- 防止历史连接(已失效的 SYN)导致 Server 浪费资源。如果两次,Server 一收到 SYN 就建立连接,但这个 SYN 可能是网络延迟的旧包。
- 确认双方都能收发:第三次 ACK 让 Server 知道 Client 能收到自己的包。

**为什么不是四次?** SYN+ACK 可以合并,没必要分两次发。

#### 4. 四次挥手

```
Client -> Server: FIN, seq=u            (FIN_WAIT_1)
Server -> Client: ACK, ack=u+1          (CLOSE_WAIT)
Server -> Client: FIN, seq=v            (LAST_ACK)
Client -> Server: ACK, ack=v+1          (TIME_WAIT -> 2MSL 后 CLOSED)
```

**为什么四次?** Server 收到 FIN 后,可能还有数据没发完,先 ACK,等数据发完再 FIN,所以 ACK 和 FIN 分开。

**TIME_WAIT 的作用**:
- 确保 Server 收到最后一个 ACK(若没收到,Server 重发 FIN)。
- 让本次连接的旧报文在网络中消散(2MSL),防止干扰新连接。

**TIME_WAIT 过多怎么办?**
- 调小 `tcp_max_tw_buckets`。
- 开启 `tcp_tw_reuse`(Client 端复用 TIME_WAIT 连接)。
- 使用长连接。

#### 5. DNS 解析流程

浏览器输入 `www.example.com` 后:

1. **浏览器缓存** -> **OS 缓存 (hosts)** -> **本地 DNS 服务器(运营商)**
2. 本地 DNS **递归查询**:
   - 问**根域名服务器**(.):返回顶级域名 (.com) 服务器地址。
   - 问**顶级域名服务器** (.com):返回权威域名服务器地址。
   - 问**权威域名服务器** (example.com):返回最终 IP。
3. 本地 DNS 缓存结果并返回给浏览器。

**递归 vs 迭代**:客户端到本地 DNS 是递归(你帮我查到底),本地 DNS 到各级是迭代(告诉我下一步去哪查)。

</details>

---

### Q3 数据库:MySQL 索引/事务/锁/优化

**题目**:MySQL 索引为什么用 B+ 树?聚簇索引和覆盖索引是什么?事务的隔离级别和 MVCC?锁有哪些?如何做 SQL 优化?

<details>
<summary>展开参考答案</summary>

#### 1. B+ 树为什么适合做索引

- **对比二叉树**:树高低,磁盘 IO 次数少。
- **对比 B 树**:B+ 树非叶子节点不存数据,只存索引,**扇出更大,树更矮**;所有数据都在叶子节点,且叶子节点用双向链表相连,**范围查询极快**。
- **对比哈希**:哈希不支持范围查询和排序。
- **对比红黑树**:树太高,IO 次数多。

InnoDB 一个节点 = 一个页 (16KB),存 1000+ 个键,3 层 B+ 树可索引 1000^3 = 10 亿条记录。

#### 2. 聚簇索引 vs 非聚簇索引

- **聚簇索引 (Clustered)**:叶子节点存**整行数据**。InnoDB 的主键索引就是聚簇索引。一张表只有一个。
- **非聚簇索引 (Secondary)**:叶子节点存**主键值**。查询时需要**回表**(用主键再查一次聚簇索引)。

**覆盖索引**:查询的字段都在索引中,不需要回表。例如 `SELECT id, name FROM user WHERE name='x'`,如果 `(name)` 是索引,且包含 id(主键自动包含),则覆盖。

**索引下推 (ICP)**:MySQL 5.6+,在存储引擎层过滤,减少回表次数。

#### 3. 最左前缀原则

联合索引 `(a, b, c)`,能命中的查询:
- `a=1` ✓
- `a=1 AND b=2` ✓
- `a=1 AND b=2 AND c=3` ✓
- `b=2` ✗(跳过 a)
- `a=1 AND c=3` ✓(只用到 a 部分)

**范围查询右侧失效**:`a=1 AND b>2 AND c=3`,c 用不到索引。

#### 4. 事务 ACID 与隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|----------|------|-----------|------|
| 读未提交 (RU) | ✓ | ✓ | ✓ |
| 读已提交 (RC) | ✗ | ✓ | ✓ |
| 可重复读 (RR) | ✗ | ✗ | ✓(InnoDB 用间隙锁解决) |
| 串行化 (Serializable) | ✗ | ✗ | ✗ |

- **脏读**:读到未提交的数据。
- **不可重复读**:同一事务两次读同一行,结果不同(其他事务 UPDATE)。
- **幻读**:同一事务两次范围查询,行数不同(其他事务 INSERT)。

**MVCC (多版本并发控制)**:
- 每行数据有隐藏字段:`trx_id`(最近修改事务 ID)、`roll_pointer`(回滚指针)。
- 读操作通过 **ReadView** 判断版本可见性。
- RC:每次 SELECT 都生成新 ReadView(所以能看到最新提交)。
- RR:事务第一次 SELECT 时生成 ReadView,后续复用(所以可重复读)。

#### 5. 锁

- **行锁**:锁单行,InnoDB 默认基于索引,**不走索引会退化为表锁**。
- **表锁**:锁整张表,MyISAM 默认。
- **间隙锁 (Gap Lock)**:锁索引区间,防止幻读。RR 级别才有。
- **Next-Key Lock**:行锁 + 间隙锁,左开右闭 `(a, b]`。
- **意向锁**:表级,标识表中有行被锁,加速判断表锁冲突。
- **共享锁 (S)**:`SELECT ... LOCK IN SHARE MODE`。
- **排他锁 (X)**:`SELECT ... FOR UPDATE`、UPDATE/DELETE。

#### 6. 日志

- **redo log**(InnoDB):物理日志,循环写,保证**持久性**(crash-safe)。
- **undo log**(InnoDB):逻辑日志,保证**原子性**和 MVCC。
- **binlog**(Server 层):逻辑日志,追加写,用于**主从复制和数据恢复**。

**两阶段提交**:redo log prepare -> binlog write -> redo log commit。保证 redo 和 binlog 一致。

#### 7. SQL 优化

- `explain` 看 type(至少 range,最好 ref/const)、rows、Extra(Using index 表示覆盖索引;Using filesort/temporary 要优化)。
- 避免 `SELECT *`,只查需要的列。
- 避免在索引列上做运算或函数。
- `LIKE 'xxx%'` 能用索引,`LIKE '%xxx'` 不能。
- 避免隐式类型转换(字符串字段 `WHERE age=18` 会让 age 失效)。
- 大分页:`WHERE id > last_id LIMIT 10` 代替 `LIMIT 1000000, 10`。
- 联合索引遵循最左前缀。

</details>

---

### Q4 Redis:数据结构/持久化/缓存问题/分布式锁

**题目**:Redis 有哪些数据结构?RDB 和 AOF 怎么选?缓存穿透/击穿/雪崩怎么解决?如何实现分布式锁?LRU 怎么实现?

<details>
<summary>展开参考答案</summary>

#### 1. 数据结构与底层

| 类型 | 底层结构 | 典型场景 |
|------|---------|---------|
| String | SDS(预分配,二进制安全) | 计数器、缓存对象 |
| List | quicklist(双向链表 + 压缩列表) | 消息队列、最新 N 条 |
| Hash | ziplist / hashtable | 对象存储 |
| Set | intset / hashtable | 标签、共同好友 |
| Zset | ziplist / **跳表 + dict** | 排行榜、延迟队列 |
| 特殊:Bitmap、HyperLogLog、GeoHash、Stream | - | 签到、UV、附近的人、消息流 |

**为什么 Zset 用跳表而不是红黑树?**
- 跳表实现简单(链表 + 多级索引),内存可控。
- 范围查询方便(链表顺序遍历)。
- 红/黑树范围查询需要中序遍历,实现复杂。

#### 2. 持久化

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| RDB | 全量快照,bgsave fork 子进程 | 恢复快,文件小 | 丢失最后一次快照后的数据 |
| AOF | 追加写命令,可 appendfsync | 数据安全性高 | 文件大,恢复慢 |
| 混合 | RDB 做全量 + AOF 做增量(4.0+) | 兼顾速度与安全 | - |

**AOF 三种策略**:
- `always`:每次写都 fsync,最安全最慢。
- `everysec`:每秒 fsync(默认),最多丢 1 秒。
- `no`:由 OS 决定,最快但不安全。

**AOF 重写**:fork 子进程,根据当前内存状态生成最小命令集,压缩文件。

#### 3. 缓存问题

| 问题 | 描述 | 解决 |
|------|------|------|
| **穿透** | 查询不存在的数据,绕过缓存打 DB | 布隆过滤器拦截;缓存空值(短 TTL) |
| **击穿** | 热点 key 过期,瞬间大量请求打 DB | 互斥锁(只放一个去查 DB);热点 key 永不过期,后台异步更新 |
| **雪崩** | 大量 key 同时过期,或 Redis 宕机 | TTL 加随机抖动;Redis 高可用(主从+哨兵);多级缓存;限流降级 |

#### 4. 分布式锁

**朴素版**:
```
SET lock_key unique_value NX PX 30000
```
- `NX`:不存在才设置。
- `PX 30000`:30 秒过期,防止死锁。
- `unique_value`:唯一标识,释放锁时校验,防止误删别人的锁。

**释放锁(原子)**:用 Lua 脚本,GET + DEL 一起执行。

**问题**:
- 业务执行超过锁过期时间,锁被别人拿走 -> **Redisson 看门狗 (watchdog)** 自动续期。
- 主从切换丢锁 -> **RedLock**(向多个独立 Redis 节点申请,多数成功才算成功),但有争议(Martin Kleppmann 质疑)。

**生产推荐**:Redisson 的 `RLock`,内置看门狗、可重入、公平锁。

#### 5. 过期与淘汰

- **过期策略**:**惰性删除**(访问时检查)+ **定期删除**(每隔一段时间随机抽样清理)。
- **淘汰策略**(maxmemory-policy):
  - `noeviction`:不淘汰,写报错(默认)。
  - `allkeys-lru` / `volatile-lru`:LRU。
  - `allkeys-lfu` / `volatile-lfu`:LFU(4.0+)。
  - `allkeys-random` / `volatile-random`:随机。
  - `volatile-ttl`:优先淘汰快过期的。

#### 6. LRU 实现

Redis 的 LRU 是**近似 LRU**:不维护全局链表(太贵),而是每次淘汰时**随机采样 5 个 key**(可配置),淘汰最久未用的。

**手写 LRU**(面试常考):

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)  # 移到末尾表示最近使用
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # 弹出头部(最久未用)
```

底层是**哈希表 + 双向链表**:哈希表 O(1) 查找,双向链表 O(1) 调整顺序。

</details>

---

### Q5 并发编程:线程池/锁/volatile/CAS/AQS

**题目**:线程池有哪些参数?工作流程是什么?拒绝策略有哪些?synchronized 和 ReentrantLock 区别?volatile 和 CAS?AQS 原理?

<details>
<summary>展开参考答案</summary>

#### 1. 线程池七参数

```java
new ThreadPoolExecutor(
    int corePoolSize,        // 核心线程数
    int maximumPoolSize,     // 最大线程数
    long keepAliveTime,      // 非核心线程空闲存活时间
    TimeUnit unit,           // 时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,        // 线程工厂
    RejectedExecutionHandler handler    // 拒绝策略
);
```

#### 2. 工作流程(重点)

1. 任务到来,若**当前线程数 < corePoolSize**,创建核心线程执行。
2. 若**当前线程数 >= corePoolSize**,任务进入**队列**。
3. 若**队列满**,且**当前线程数 < maximumPoolSize**,创建非核心线程执行。
4. 若**队列满且线程数 = maximumPoolSize**,触发**拒绝策略**。

**注意**:不是先创建到最大线程数再入队,而是**先入队再扩容**。这是常见误区。

#### 3. 四种拒绝策略

| 策略 | 行为 |
|------|------|
| AbortPolicy | 抛 RejectedExecutionException(默认) |
| CallerRunsPolicy | 由提交任务的线程执行该任务(降速) |
| DiscardPolicy | 直接丢弃 |
| DiscardOldestPolicy | 丢弃队列最老的任务,再尝试提交 |

#### 4. 线程数配置经验

- **CPU 密集型**:`N + 1`(N = CPU 核数),+1 防止偶发的页缺失或线程暂停。
- **IO 密集型**:`2N` 或 `N * (1 + 等待时间/计算时间)`。
- **混合型**:拆分成 CPU 密集和 IO 密集两个池。

**不要用 Executors 的快捷方法**(FixedThreadPool、CachedThreadPool)——它们要么队列无界(OOM),要么线程数无界(资源耗尽)。阿里规约强制用 ThreadPoolExecutor。

#### 5. synchronized vs ReentrantLock

| 维度 | synchronized | ReentrantLock |
|------|--------------|---------------|
| 实现 | JVM 层(monitorenter/exit) | JDK 层(AQS) |
| 锁释放 | 自动(出代码块) | 手动 unlock,需 finally |
| 可中断 | 否 | `lockInterruptibly()` 可响应中断 |
| 可超时 | 否 | `tryLock(timeout)` |
| 公平锁 | 非公平 | 可选公平/非公平 |
| 条件变量 | 1 个(wait/notify) | 多个 Condition |
| 性能 | JDK 6+ 优化(偏向->轻量->重量),差距小 | 灵活但稍复杂 |

#### 6. volatile

两个语义:
1. **可见性**:写 volatile 变量,强制刷回主内存;读 volatile 变量,强制从主内存读。其他线程能立即看到更新。
2. **禁止指令重排序**:插入**内存屏障**(LoadLoad / StoreStore / LoadStore / StoreLoad)。

**不保证原子性**:`i++` 即使 i 是 volatile 也线程不安全,需要 `AtomicInteger` 或加锁。

**典型应用**:DCL 单例的实例字段必须 volatile,防止"构造指令重排到分配内存之前"导致拿到未初始化对象。

#### 7. CAS 与 ABA

**CAS (Compare And Swap)**:三个操作数——内存值 V、期望值 E、新值 N。若 V == E,则 V = N,否则重试。硬件级别 `cmpxchg` 指令保证原子。

**问题**:
- **ABA 问题**:A -> B -> A,CAS 认为没变过。解决:版本号(`AtomicStampedReference`)。
- **自旋开销**:失败重试消耗 CPU。解决:限制自旋次数,或用 LongAdder 分段累加。
- **只能保证一个变量原子**:多个变量用锁或 `AtomicReference` 封装成对象。

#### 8. AQS (AbstractQueuedSynchronizer)

JUC 锁与同步器的基础框架(ReentrantLock、Semaphore、CountDownLatch、ReentrantReadWriteLock 都基于它)。

- **state**(volatile int):表示同步状态,子类定义含义(ReentrantLock 中是重入次数)。
- **CLH 队列**(双向链表):等待获取锁的线程封装成 Node 入队,前驱节点释放后唤醒后继。
- **两种模式**:
  - **独占**:ReentrantLock,同一时刻一个线程持有。`tryAcquire/tryRelease`。
  - **共享**:Semaphore/CountDownLatch,多个线程可同时获取。`tryAcquireShared/tryReleaseShared`。
- **模板方法模式**:AQS 定义流程,子类实现 tryXxx。

#### 9. 并发容器

- **ConcurrentHashMap**:JDK 8 后是 **CAS + synchronized 分段锁**(锁单个桶),并发度高于 1.7 的 Segment。
- **CopyOnWriteArrayList**:写时复制,读无锁。适合读多写少(配置列表)。
- **BlockingQueue**:`ArrayBlockingQueue`(有界数组)、`LinkedBlockingQueue`(链表,默认无界)、`SynchronousQueue`(直接交付,CachedThreadPool 用)。

</details>

---

### Q6 消息队列:Kafka/RabbitMQ/RocketMQ + 可靠性/有序/重复/堆积

**题目**:三大 MQ 怎么选?如何保证消息不丢失?如何保证消息有序?如何处理重复消费?消息堆积怎么办?

<details>
<summary>展开参考答案</summary>

#### 1. 选型对比

| 维度 | Kafka | RabbitMQ | RocketMQ |
|------|-------|----------|----------|
| 吞吐量 | 百万级/秒 | 万级/秒 | 十万级/秒 |
| 延迟 | ms 级 | us 级 | ms 级 |
| 语言 | Scala/Java | Erlang | Java |
| 顺序性 | 分区内有序 | 单队列有序 | 分区内有序 |
| 事务消息 | 弱(0.11+) | 弱 | **强(半消息+回查)** |
| 适用场景 | 日志、大数据、流处理 | 企业级路由、复杂业务 | 金融、电商事务 |

#### 2. 消息可靠性(不丢失)

三个环节:

**生产端**:
- Kafka:`acks=all`(所有副本确认)+ `retries>0` + `enable.idempotence=true`(幂等避免重试重复)。
- RabbitMQ:开启 `confirm` 模式,确认到达 Broker。
- RocketMQ:同步发送 + 重试,或使用事务消息。

**Broker**:
- 持久化:Kafka 副本数 >= 2;RabbitMQ 队列 `durable=true`,消息 `deliveryMode=2`;RocketMQ 默认同步刷盘。
- 同步刷盘 vs 异步刷盘:同步更安全更慢。

**消费端**:
- 关闭自动 ack,业务处理完再手动 ack。
- 消费失败重试 + 死信队列(DLQ)兜底。

#### 3. 消息有序性

**全局有序**:单分区/单队列,牺牲并发。基本不用。

**分区有序**(常用):
- Kafka:同一业务 key 的消息发到同一 partition(用 key hash)。消费时单线程消费一个分区。
- 若要并行消费又有序:按业务 key 取模分片到多个队列,每个队列单线程消费。

**坑**:消费端多线程会打乱顺序。解决:消费端按 key hash 到不同线程(ShardingExecutor)。

#### 4. 重复消费(幂等)

网络问题导致 ack 丢失,Broker 会重投。**消费端必须幂等**。

**方案**:
- **唯一键去重**:数据库唯一索引,插入失败说明已处理。
- **状态机**:业务状态只能往前推进,重复消息查状态即可。
- **Redis 标记**:SETNX 业务唯一键,过期时间合理。
- **Token 机制**:前端每次请求带唯一 token,后端校验。

#### 5. 消息堆积

原因:消费速度 < 生产速度,或消费失败一直重试。

**处理**:
- **临时扩容**:增加 consumer 实例(注意不能超过分区数,Kafka 中超出的实例空闲)。
- **丢弃非关键消息**:死信 + 报警。
- **跳过堆积**:把堆积消息转储到新 topic,慢慢处理,主 topic 恢复实时消费。
- **优化消费逻辑**:批量处理、异步化、减少 DB 操作、引入缓存。
- **根本**:消费端 RT 要低于生产端发送间隔,否则早晚堆积。

#### 6. 与 Agent 场景的结合

Agent 编排中,MQ 用于:
- **任务解耦**:用户提交 Agent 任务 -> 入队 -> Worker 消费执行。
- **多 Agent 协作**:Agent A 的输出作为 Agent B 的输入,通过 topic 转发。
- **失败重试**:LLM 调用失败的消息进重试队列,带退避策略。
- **死信告警**:超过 N 次重试的消息进 DLQ,触发人工介入。

</details>

---

### Q7 微服务:注册/网关/熔断/分布式事务

**题目**:微服务核心组件有哪些?熔断降级怎么实现?分布式事务有哪些方案?各自的适用场景?

<details>
<summary>展开参考答案</summary>

#### 1. 微服务核心组件

| 组件 | 作用 | 代表实现 |
|------|------|---------|
| 服务注册发现 | 服务上下线自动感知 | Nacos / Eureka / Consul / Zookeeper |
| 负载均衡 | 请求分发 | Ribbon / LoadBalancer / Nginx |
| 配置中心 | 配置集中 + 热更新 | Nacos / Apollo / Spring Cloud Config |
| API 网关 | 统一入口、鉴权、限流、路由 | Spring Cloud Gateway / Zuul / Kong |
| 熔断降级 | 防止雪崩 | Sentinel / Hystrix / Resilience4j |
| 链路追踪 | 跨服务调用可视化 | SkyWalking / Zipkin / Jaeger |
| 消息队列 | 解耦削峰 | Kafka / RocketMQ / RabbitMQ |
| 日志聚合 | 集中查询 | ELK / Loki |

#### 2. 服务注册发现

- **CP vs AP**:Zookeeper/Consul 偏 CP(强一致),Nacos/Eureka 偏 AP(高可用,允许短时不一致)。
- 微服务多选 AP,因为服务列表短时不一致不影响业务,但不可用是致命的。
- **健康检查**:心跳续约,超时剔除。

#### 3. 负载均衡

- **客户端负载**:Ribbon,consumer 内部从注册中心拉列表,自己选(省一跳)。
- **服务端负载**:Nginx,统一入口。
- **算法**:轮询、加权轮询、随机、最少连接、一致性哈希(用于会话保持)。

#### 4. 熔断降级限流

**熔断**:下游服务异常率/慢调用率达到阈值,**直接快速失败**,不再请求下游,给下游恢复时间。
- 三状态:**Closed(正常) -> Open(熔断) -> Half-Open(半开,放少量请求试探)**。

**降级**:熔断后返回兜底数据(默认值、缓存、友好提示)。

**限流**:保护自己不被打垮。算法:
- **计数器**:固定窗口,临界点会突刺。
- **滑动窗口**:解决临界突刺。
- **漏桶**:恒定速率出水,超出排队或丢弃。
- **令牌桶**:恒定速率发令牌,允许突发(令牌可累积)。

Sentinel vs Hystrix:Hystrix 已停止维护,Sentinel 阿里开源,支持流控+熔断+热点+系统自适应,推荐。

#### 5. 链路追踪

- **TraceId**:一次请求贯穿全链路。
- **SpanId**:每个服务调用一个 Span,记录耗时。
- 实现:TraceContext 通过 HTTP Header(Sleuth)或 RPC 元数据透传。
- 采样:全量上报影响性能,通常采样 1%-10%,慢请求必采。

#### 6. 分布式事务

| 方案 | 一致性 | 复杂度 | 适用 |
|------|--------|--------|------|
| **2PC** | 强一致 | 中,XA 协议 | 数据库层,性能差 |
| **3PC** | 强一致 | 高,有超时 | 学术,少用 |
| **TCC** | 强一致 | 高,业务侵入 | 资金、订单 |
| **Saga** | 最终一致 | 中,长事务 | 业务流程长 |
| **本地消息表** | 最终一致 | 低 | 异步解耦 |
| **事务消息** | 最终一致 | 低 | RocketMQ 原生支持 |
| **最大努力通知** | 最终一致 | 低 | 对账、通知 |

**2PC**:协调者 prepare -> 参与者锁资源 -> 协调者 commit/rollback。问题:协调者单点、参与者阻塞、数据不一致(协调者 commit 后挂掉)。

**TCC**:Try(预留资源) -> Confirm(确认) -> Cancel(回滚)。每个业务要实现三个接口,侵入大但灵活。

**Saga**:长事务拆成多个本地事务,每个有补偿动作。失败时按反向补偿。

**本地消息表**:业务表 + 消息表同事务写入,后台扫消息表发 MQ。天然最终一致,最常用。

**事务消息(RocketMQ)**:发送半消息(对 consumer 不可见)-> 执行本地事务 -> commit/rollback。若超时未 commit,Broker 回查 producer。

#### 7. 与 Agent 场景的结合

Agent 服务里:
- **网关**:统一鉴权(API Key/JWT)、限流(每用户 QPS)、路由到不同 Agent 模型。
- **熔断**:LLM 调用超时率高达 1% 时熔断,返回缓存或降级模型。
- **链路追踪**:一次 Agent 调用涉及多步工具调用,TraceId 串联全链路用于调试。
- **分布式事务**:Agent 执行 + 扣费 + 日志记录,用本地消息表保证一致。

</details>

---

### Q8 系统设计:短链/秒杀/Feed 流(选短链详细展开)

**题目**:设计一个短链系统、秒杀系统、Feed 流系统,选一个详细展开。

<details>
<summary>展开参考答案(短链系统)</summary>

> 三个都是经典题,篇幅所限这里**详细展开短链系统**。秒杀和 Feed 流给出骨架。

#### 设计短链系统

**需求**:
- 给长 URL 生成短码(如 `https://t.co/x7Yz9K`)。
- 点击短链跳转到原 URL(301 永久 / 302 临时)。
- 支持访问统计(PV/UV)。
- 短码不可猜测。

**估算**(假设 1 亿活跃用户,每人每天生成 1 条):
- 写 QPS:1 亿 / 86400 ≈ 1.2k,峰值 5x ≈ 6k。
- 读 QPS:写读比 10:1,约 12k 峰值 60k。
- 存储:1 亿/天 * 365 * 5 年 = 1825 亿条,每条 500 字节 ≈ 90 TB。

**短码生成方案**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| 自增 ID + 62 进制(MD5 截断也类似) | 简单,无冲突 | 可预测,爬虫可遍历 |
| 哈希(MD5/MurmurHash)取前 6-8 位 | 不可预测 | 可能冲突,需查库去重 |
| 预生成号段(发号器) | 高性能 | 短码与时间相关,有规律 |
| 随机生成 + 布隆过滤器去重 | 不可预测 | 冲突需重试 |

**推荐**:发号器(Snowflake 或 Redis incr)+ 62 进制编码,6 位可表示 62^6 ≈ 568 亿,够用。若担心可预测,加随机盐再哈希一次。

**存储**:
- MySQL:短码(主键) -> 长 URL,带创建时间、过期时间、用户 ID。分库分表(短码 hash)。
- Redis:缓存热点短链,降低 DB 压力。

**跳转流程**:
1. 用户访问 `t.co/x7Yz9K`。
2. 网关解析短码,查 Redis;未命中查 DB。
3. 302 跳转到长 URL(302 便于统计,301 会被浏览器缓存导致漏统计)。
4. 异步写访问日志(Kafka -> 数仓)。

**缓存策略**:
- 热门短链 Redis 缓存,TTL 1 小时。
- 缓存穿透:不存在的短码缓存空值。

**分库分表**:
- 90 TB 单库扛不住。按短码 hash 分 64 库,每库 ~1.4 TB。
- 历史数据冷热分离:6 个月前的转 OSS/对象存储。

**高可用**:
- 多机房部署,DNS 智能解析。
- 短码生成器单点:Snowflake 不依赖中心,Redis incr 配合主从 + 哨兵。

#### 秒杀系统(骨架)

- **前端**:静态化(CDN)、按钮防抖、答题验证、倒计时。
- **网关**:限流(IP/用户/全局)、黑名单。
- **服务层**:库存预扣(Redis Lua 原子)、异步下单(MQ 削峰)。
- **存储**:Redis 缓存库存,DB 用乐观锁 `UPDATE stock SET n=n-1 WHERE id=? AND n>0`。
- **防超卖**:Redis Lua + DB 双重校验。
- **热点**:库存分桶(100 库存拆成 10 个桶,减少热点 key)。

#### Feed 流系统(骨架)

- **拉模式**:用户查看时实时聚合关注人的最新微博。读放大,适合冷启动。
- **推模式**:发布时推到所有粉丝收件箱。写放大,适合粉丝少(大 V 例外)。
- **推拉结合**:大 V 拉普通用户推。微博、抖音都用这种。
- **存储**:Redis Zset(按时间排序的收件箱)+ MySQL 持久化。

</details>

---

### Q9 手撕代码:实现一个简单线程池(Python)

**题目**:用 Python 实现一个简单的线程池,包含任务队列、工作线程、拒绝策略、优雅关闭。

<details>
<summary>展开参考答案</summary>

```python
import threading
import queue
import time
from enum import Enum


class RejectPolicy(Enum):
    ABORT = "abort"        # 抛异常
    CALLER_RUNS = "caller" # 调用者线程执行
    DISCARD = "discard"    # 丢弃
    DISCARD_OLDEST = "oldest"  # 丢弃最旧的


class ThreadPool:
    """
    简化版线程池,模拟 Java ThreadPoolExecutor:
    - core 线程数 + max 线程数 + 有界队列 + 拒绝策略
    - 优雅关闭: shutdown() 等待任务完成; shutdown_now() 立即停止
    """

    def __init__(self, core_size, max_size, queue_capacity,
                 keep_alive=30, reject_policy=RejectPolicy.ABORT):
        self.core_size = core_size
        self.max_size = max_size
        self.queue_capacity = queue_capacity
        self.keep_alive = keep_alive
        self.reject_policy = reject_policy

        self._task_queue = queue.Queue(maxsize=queue_capacity)
        self._workers = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._shutdown_now = False
        self._idle_event = threading.Event()
        self._idle_event.set()  # 一开始没有任务

        # 预创建核心线程
        for _ in range(core_size):
            self._add_worker(core=True)

    def _add_worker(self, core):
        """创建并启动一个工作线程"""
        with self._lock:
            if self._shutdown:
                return False
            if core and len(self._workers) >= self.core_size:
                return False
            if not core and len(self._workers) >= self.max_size:
                return False
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)
            return True

    def _worker_loop(self):
        """工作线程主循环"""
        while True:
            try:
                # 非核心线程用超时获取,超时则退出
                timeout = None
                if len(self._workers) > self.core_size:
                    timeout = self.keep_alive
                task = self._task_queue.get(timeout=timeout)
            except queue.Empty:
                # 非核心线程空闲超时,退出
                with self._lock:
                    # 简化处理:不精确移除自己,实际应记录当前线程
                    pass
                return

            if task is None:
                # 关闭信号
                return

            try:
                task()
            except Exception as e:
                print(f"[worker] task error: {e}")
            finally:
                self._task_queue.task_done()
                if self._task_queue.unfinished_tasks == 0:
                    self._idle_event.set()

    def execute(self, task):
        """提交任务"""
        if self._shutdown:
            raise RuntimeError("ThreadPool has been shutdown")

        # 1. 核心线程未满,直接创建
        if len(self._workers) < self.core_size:
            if self._add_worker(core=True):
                self._idle_event.clear()
                self._task_queue.put(task)
                return

        # 2. 队列未满,入队
        try:
            self._task_queue.put_nowait(task)
            self._idle_event.clear()
            return
        except queue.Full:
            pass

        # 3. 队列满,尝试创建非核心线程
        if self._add_worker(core=False):
            self._task_queue.put(task)
            return

        # 4. 触发拒绝策略
        self._reject(task)

    def _reject(self, task):
        if self.reject_policy == RejectPolicy.ABORT:
            raise RuntimeError("Task rejected: pool full")
        elif self.reject_policy == RejectPolicy.CALLER_RUNS:
            task()  # 调用者线程自己跑
        elif self.reject_policy == RejectPolicy.DISCARD:
            print("[reject] task discarded")
        elif self.reject_policy == RejectPolicy.DISCARD_OLDEST:
            try:
                self._task_queue.get_nowait()
                self._task_queue.put_nowait(task)
            except queue.Empty:
                pass

    def shutdown(self, wait=True):
        """优雅关闭:不再接受新任务,等待已提交任务完成"""
        self._shutdown = True
        # 往队列塞 None 让 worker 退出
        for _ in range(len(self._workers)):
            self._task_queue.put(None)
        if wait:
            self._task_queue.join()
            for t in self._workers:
                t.join()

    def shutdown_now(self):
        """立即关闭"""
        self._shutdown = True
        self._shutdown_now = True
        # 清空队列
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break
        for _ in range(len(self._workers)):
            self._task_queue.put(None)

    def await_termination(self, timeout=None):
        """等待所有任务完成"""
        return self._idle_event.wait(timeout)


# ---------- 测试 ----------
if __name__ == "__main__":
    def task(i):
        print(f"[task {i}] start on {threading.current_thread().name}")
        time.sleep(0.5)
        print(f"[task {i}] done")

    pool = ThreadPool(core_size=2, max_size=4,
                      queue_capacity=2,
                      reject_policy=RejectPolicy.CALLER_RUNS)

    for i in range(10):
        try:
            pool.execute(lambda x=i: task(x))
        except Exception as e:
            print(f"[main] rejected: {e}")

    pool.shutdown(wait=True)
    print("[main] pool closed")
```

**面试官追问点**:
1. 为什么任务队列用有界?(防止 OOM,但会触发拒绝)
2. 如何实现线程池的监控?(暴露活跃线程数、队列大小、完成任务数等指标)
3. CallerRunsPolicy 的妙用?(让提交者变慢,自然反压)
4. Python 的 GIL 对线程池的影响?(CPU 密集任务用 `ProcessPoolExecutor`,IO 密集用线程池即可)
5. 如何优雅关闭?(先 stop 接收,再等队列消费完,再 stop 线程)

</details>

---

### Q10 系统设计:设计一个 Agent 服务后端架构

**题目**:设计一个 Agent 服务后端架构,包含 API 层、Agent 引擎、工具服务、消息队列、数据库、缓存、监控。需要支持流式输出、长任务、多 Agent 协作。

<details>
<summary>展开参考答案</summary>

#### 1. 需求拆解

**功能需求**:
- 用户通过 API 提交 Agent 任务(自然语言输入)。
- Agent 调用 LLM、工具(搜索/代码执行/数据库查询),多步推理。
- 支持流式输出(SSE),边生成边返回。
- 长任务(分钟级)异步执行,完成后回调或查询。
- 多 Agent 协作(主 Agent 调度子 Agent)。
- 会话历史持久化,支持上下文。

**非功能需求**:
- QPS:推理慢,主要瓶颈在 LLM,假设 100 QPS 提交,500 QPS SSE 长连接。
- 延迟:首 token < 2s,完整响应 < 30s。
- 可用性:99.9%,LLM 故障要降级。
- 成本:LLM 调用贵,需要缓存。

#### 2. 整体架构

```
                          ┌──────────────────┐
                          │   CDN / WAF      │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  API Gateway     │  鉴权 / 限流 / 路由
                          │  (Spring Cloud   │
                          │   Gateway / Kong)│
                          └────────┬─────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
       ┌────────▼───────┐ ┌────────▼───────┐ ┌────────▼───────┐
       │ Session Service│ │ Agent Service  │ │ Tool Service   │
       │ (会话管理)     │ │ (Agent 编排)   │ │ (工具调用)     │
       │ - 创建/查询    │ │ - ReAct/Plan   │ │ - 搜索/代码    │
       │ - 历史存储     │ │ - 多Agent调度  │ │ - DB查询       │
       └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
                │                  │                  │
                │           ┌──────▼──────┐           │
                │           │ LLM Gateway │           │
                │           │ (模型路由/   │           │
                │           │  降级/重试)  │           │
                │           └──────┬──────┘           │
                │                  │                  │
       ┌────────▼──────────────────▼──────────────────▼────┐
       │              消息队列 (Kafka/RocketMQ)             │
       │   topics: agent-task / tool-call / llm-call       │
       └────────┬──────────────────────────────────────────┘
                │
       ┌────────▼──────────────────────────────────────────┐
       │  存储层                                             │
       │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
       │  │ MySQL    │ │ Redis    │ │ 向量库   │           │
       │  │ 业务/会话│ │ 缓存/锁  │ │ Milvus/  │           │
       │  │          │ │ /队列    │ │ PgVector │           │
       │  └──────────┘ └──────────┘ └──────────┘           │
       └────────────────────────────────────────────────────┘
                │
       ┌────────▼──────────────────────────────────────────┐
       │  可观测性                                           │
       │  Prometheus + Grafana + Loki + SkyWalking + 告警   │
       └────────────────────────────────────────────────────┘
```

#### 3. 核心模块设计

##### 3.1 API 层

- **同步接口** `/v1/agents/{id}/chat`(短任务,直接返回)。
- **流式接口** `/v1/agents/{id}/chat/stream`(SSE,首 token < 2s)。
- **异步接口** `/v1/agents/{id}/tasks`(POST 提交长任务,返回 task_id;GET `/tasks/{task_id}` 查询状态/结果;支持 webhook 回调)。
- **鉴权**:API Key + JWT,网关层校验。
- **限流**:用户级 QPS(令牌桶),防止恶意调用刷成本。

##### 3.2 Agent 引擎

- **编排模式**:ReAct(推理-行动-观察循环)、Plan-and-Execute(先规划再执行)、多 Agent 协作(supervisor + workers)。
- **状态管理**:Agent 每步的 thought/action/observation 持久化到 MySQL + Redis(活跃会话快照)。
- **断点续跑**:长任务每步 checkpoint,失败可从最近 checkpoint 恢复。
- **超时控制**:单步 LLM 调用 30s 超时,整体任务 5 分钟超时,超时进入"暂停"状态,可手动 resume。
- **重试策略**:LLM 调用失败,指数退避重试 3 次;工具调用失败,重试 1 次后降级。

##### 3.3 LLM Gateway(关键)

为什么单独抽一层?
- **多模型路由**:简单问题走小模型(便宜快),复杂问题走大模型;按用户套餐路由。
- **降级**:主模型故障(OpenAI 挂了)自动切备用(Anthropic / 本地模型)。
- **重试与超时**:统一处理,业务层无感。
- **成本控制**:Token 计数、配额校验、按用户/团队限流。
- **语义缓存**:相似 query 命中缓存(GPTCache 思路),节省 30%+ 成本。
- **审计日志**:所有 LLM 调用记录,便于回溯和合规。

##### 3.4 工具服务

- **工具注册**:每个工具有 schema(name、description、parameters JSON Schema),Agent 通过 function calling 选择。
- **工具执行**:同步工具直接调用;异步工具(耗时)入 MQ,worker 执行,结果回写 Agent。
- **沙箱**:代码执行工具用 Docker 容器或 Firecracker microVM 隔离,防止恶意代码。
- **权限**:不同 Agent 实例有不同的工具白名单(防止越权)。

##### 3.5 消息队列

- `agent-task` topic:用户提交的 Agent 任务,worker 消费。
- `tool-call` topic:Agent -> 工具服务的调用(异步工具)。
- `llm-call` topic:可选,LLM 调用事件用于监控和缓存预热。
- `dead-letter` topic:超过重试次数的消息,触发告警。

**为什么用 MQ?**
- 削峰:LLM 慢,直接同步会堆积,MQ 缓冲。
- 解耦:Agent 引擎、工具服务、LLM 网关独立扩缩容。
- 重试:消费失败自动重投,带退避。

##### 3.6 存储层

| 存储 | 用途 | 数据 |
|------|------|------|
| MySQL | 业务数据 | 用户、会话、任务、计费 |
| Redis | 缓存 + 实时状态 | 会话快照、分布式锁、限流计数、SSE 消息中转(pub/sub) |
| 向量库 | 语义检索 | 会话历史 embedding(长期记忆)、知识库 |
| 对象存储 | 大文件 | Agent 产出物(图片、文档)、日志归档 |
| 时序库 | 监控 | Prometheus,LLM 调用延迟、Token 用量 |

##### 3.7 流式输出实现

SSE 难点:LLM Gateway 在远端,API Gateway 到用户是长连接。

**方案**:
1. 用户 -> API Gateway(SSE 长连接)。
2. API Gateway -> Agent Service(HTTP 调用)。
3. Agent Service -> LLM Gateway(SSE 流式接收)。
4. 每个 token 经 Agent Service 透传给 API Gateway -> 用户。

**多实例问题**:Agent Service 多实例,用户连接在实例 A,但任务被实例 B 消费。解决:
- 用 **Redis pub/sub** 做消息中转:实例 B 把 token 发到 `channel:task_id`,实例 A 订阅推给用户。
- 或用 **Kafka**,实例 A 消费 `task_id` 对应的 partition。

##### 3.8 长任务处理

- 用户 POST 提交 -> 生成 task_id -> 入 MQ -> 返回 task_id。
- Worker 消费 -> 执行 Agent -> 状态更新到 MySQL + Redis。
- 用户轮询 `GET /tasks/{task_id}`,或注册 webhook,完成后回调。
- 状态机:`pending -> running -> success / failed / timeout / cancelled`。

##### 3.9 多 Agent 协作

- **supervisor 模式**:主 Agent 拆解任务,分发给子 Agent,汇总结果。
- **通信**:通过共享 Redis(消息邮箱)或 MQ topic。
- **隔离**:子 Agent 有独立 context,避免污染主 Agent。
- **超时**:子 Agent 超时不阻塞主 Agent,主 Agent 决定重试或降级。

##### 3.10 可观测性

- **指标**:QPS、首 token 延迟、完整响应延迟、LLM 调用成功率、Token 消耗、工具调用次数、任务完成率。
- **链路追踪**:一次 Agent 任务生成 TraceId,贯穿 LLM 调用、工具调用、DB 查询,用 SkyWalking 可视化每步耗时。
- **日志**:结构化日志(JSON),含 task_id、user_id、step,集中到 Loki/ELK。
- **告警**:LLM 错误率 > 5%、首 token P99 > 5s、任务失败率 > 10%,触发 PagerDuty/企微告警。

#### 4. 容量与扩容

- API Gateway:无状态,水平扩容,前置 LB。
- Agent Service:CPU 密集(编排逻辑),4 核 8G 起,按 QPS 扩。
- LLM Gateway:IO 密集(等 LLM 响应),2 核 4G,大量连接,按并发数扩。
- Tool Service:按工具类型独立扩(代码执行 CPU 重,搜索 IO 重)。
- MySQL:读写分离,会话表按 user_id 分库。

#### 5. 面试加分点

- 主动提到**成本控制**(LLM 贵,语义缓存 + 模型分级)。
- 主动提到**安全**(工具沙箱、Prompt 注入防御、API Key 轮转)。
- 主动提到**降级**(LLM 故障切备用模型、工具故障返回兜底)。
- 主动提到**幂等**(任务提交支持 idempotency-key,防止重试重复执行)。
- 主动提到**多租户**(不同租户资源隔离、配额限制)。

</details>

---

## 核心知识回顾表

| 板块 | 核心考点 | 一句话记忆 |
|------|---------|-----------|
| OS | epoll | 红黑树存 fd,就绪链表回调,O(1) |
| OS | 死锁四条件 | 互斥/占有等待/不剥夺/循环等待 |
| 网络 | 三次握手 | 防历史连接 + 确认双向收发 |
| 网络 | TIME_WAIT | 确保最后 ACK 到达 + 旧报文消散 |
| MySQL | B+ 树 | 非叶子只存索引,叶子链表,范围查询快 |
| MySQL | MVCC | 行版本 + ReadView,RR 复用、RC 重建 |
| Redis | 缓存三问题 | 穿透=布隆/空值,击穿=互斥锁,雪崩=随机 TTL |
| Redis | 分布式锁 | SET NX PX + 唯一值 + Lua 释放 |
| 并发 | 线程池流程 | 核心->队列->非核心->拒绝 |
| 并发 | volatile | 可见性 + 禁重排,不保证原子 |
| 并发 | AQS | state + CLH 队列 + 模板方法 |
| MQ | 可靠性 | 生产确认 + 持久化 + 消费手动 ack |
| MQ | 有序性 | 同 key 同分区 + 单线程消费 |
| 微服务 | 熔断三态 | Closed -> Open -> Half-Open |
| 微服务 | 分布式事务 | 强一致用 TCC,最终一致用本地消息表 |
| 系统设计 | 短链 | 发号器 + 62 进制 + Redis 缓存 |
| 系统设计 | Agent 后端 | API/引擎/工具/MQ/存储/监控六层 |

---

## 面试速记卡

> 撕下来贴墙上的那种,每天瞄一眼。

```
┌──────────────────────────────────────────────────────────┐
│ 后端八股 TOP 20 速记                                       │
├──────────────────────────────────────────────────────────┤
│ 1. 进程=资源,线程=调度,协程=用户态                        │
│ 2. epoll:红黑树+就绪链表,O(1),ET 需配非阻塞              │
│ 3. 死锁四件套:互斥/占等/不剥/循环                          │
│ 4. TCP 可靠:序号+确认+重传+流控+拥塞                       │
│ 5. 三次握手:防历史连接,确认双向                            │
│ 6. TIME_WAIT 2MSL:等最后 ACK + 消散旧包                   │
│ 7. B+树:非叶子纯索引,叶子双向链表,3 层 10 亿              │
│ 8. 聚簇索引:叶子存整行,只有 1 个;非聚簇要回表             │
│ 9. MVCC:行版本+ReadView,RR 复用 RC 重建                   │
│ 10. 缓存穿透=布隆,击穿=互斥锁,雪崩=随机TTL                │
│ 11. 分布式锁:SET NX PX + 唯一值 + Lua 释放                │
│ 12. 线程池:核心->队列->非核心->拒绝(顺序别记反)           │
│ 13. volatile:可见+禁重排,不原子;i++ 要 AtomicInteger      │
│ 14. CAS 三操作数 V/E/N,ABA 加版本号                       │
│ 15. AQS:state + CLH 双向队列,独占/共享                    │
│ 16. MQ 不丢:acks=all + 持久化 + 手动 ack                  │
│ 17. MQ 有序:同 key 同分区 + 单线程消费                    │
│ 18. 幂等:唯一键/状态机/Redis 标记/Token                   │
│ 19. 熔断:Closed->Open->Half-Open,下游保护                 │
│ 20. 分布式事务:强=TCC,最终=本地消息表(最常用)            │
└──────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

> 这些是面试中"会但答错"的高发区,反复看。

### 1. 线程池工作流程顺序

**错**:先创建到 max 线程,再入队。
**对**:**先核心 -> 再入队 -> 队列满才扩非核心 -> 满了才拒绝**。队列没满不会创建非核心线程。

### 2. volatile 不保证原子性

**错**:加了 volatile 的 `i++` 就线程安全了。
**对**:`i++` 是"读-改-写"三步,volatile 只保证读和写各自可见,中间仍可能被插入。用 `AtomicInteger` 或加锁。

### 3. Redis 分布式锁的释放

**错**:`del key` 就行。
**对**:必须先 GET 比对唯一值再 DEL,且这两步要用 **Lua 脚本**保证原子,否则可能误删别人的锁。

### 4. 聚簇索引数量

**错**:可以建多个聚簇索引。
**对**:一张表**只能有一个**聚簇索引(InnoDB 默认主键),因为数据物理上只能按一种顺序排列。其他都是二级索引。

### 5. 联合索引最左前缀

**错**:`WHERE b=2 AND a=1` 用不到 `(a,b,c)` 索引。
**对**:MySQL 优化器会**自动调整顺序**,等价于 `WHERE a=1 AND b=2`,能用。但 `WHERE b=2`(没有 a)确实用不到。

### 6. 四次挥手为什么 TIME_WAIT 在主动方

**错**:TIME_WAIT 在被动关闭方。
**对**:在**主动关闭方**。因为主动方发最后一个 ACK,要等 2MSL 确认对方收到,且让自己这一方向的旧报文消散。

### 7. InnoDB 行锁基于索引

**错**:UPDATE 一定只锁一行。
**对**:InnoDB 行锁**基于索引**,**如果 WHERE 没走索引,会退化为表锁**!这是大坑,生产事故常见原因。

### 8. Kafka 消费者数 vs 分区数

**错**:消费者越多消费越快。
**对**:消费者数**不能超过分区数**,超出的消费者空闲。要扩消费速度,先扩分区。

### 9. Redis 过期 key 不会立刻删除

**错**:TTL 到了 Redis 马上删除。
**对**:Redis 用**惰性删除 + 定期删除**。TTL 到了不一定立刻删,要等下次访问或定期扫描。所以 `dbsize` 可能包含已过期但未删的 key。

### 10. 2MSL 是多久

**错**:2MSL = 2 秒。
**对**:MSL (Maximum Segment Lifetime) 是报文最大生存时间,Linux 默认 30s,**2MSL = 60s**。这是 TIME_WAIT 持续时间。`tcp_fin_timeout` 不是控制 TIME_WAIT 的,别搞混。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 能用 30 秒讲清进程和线程的区别,并说出协程的定位
- [ ] 能画出三次握手和四次挥手的时序图,并解释每个状态
- [ ] 能解释 B+ 树为什么适合做索引(对比 B 树/哈希/红黑树)
- [ ] 能说出 MVCC 在 RC 和 RR 下的 ReadView 生成时机差异
- [ ] 能区分缓存穿透/击穿/雪崩,并给每种 2 个解决方案
- [ ] 能默写线程池 7 参数和工作流程(注意先入队再扩容)
- [ ] 能解释 volatile 的两个语义和不保证原子性的原因
- [ ] 能说出 AQS 的核心组成(state + CLH + 模板方法)
- [ ] 能对比 2PC/TCC/Saga/本地消息表的适用场景
- [ ] 能画出 Agent 服务后端架构图,说出每层职责

### 代码题(3 个)

- [ ] 手写 LRU(哈希表 + 双向链表,或 OrderedDict)
- [ ] 手写简化版线程池(任务队列 + worker + 拒绝策略 + 优雅关闭)
- [ ] 手写单例模式(DCL,注意 volatile 防止指令重排)

### 系统设计题(2 个)

- [ ] 设计短链系统(发号器 + 62 进制 + 缓存 + 302 跳转 + 分库分表)
- [ ] 设计 Agent 服务后端(API/引擎/工具/MQ/存储/监控,含流式输出和长任务)

---

## 延伸阅读

### 必读
- 《MySQL 45 讲》林晓斌 — 索引/事务/锁讲得最清楚
- 《Redis 设计与实现》黄健宏 — 数据结构底层
- 《Java 并发编程的艺术》方腾飞 — AQS/线程池深入

### 选读
- 《数据密集型应用系统设计》(DERTA) — 分布式系统圣经,强烈推荐
- 《微服务架构设计模式》Chris Richardson — 微服务 + 分布式事务
- 《Kafka 权威指南》— 消息队列原理

### 文章
- Martin Kleppmann 《How to do distributed locking》— RedLock 争议
-美团技术博客《缓存穿透/击穿/雪崩》系列
- 阿里 Sentinel Wiki — 熔断降级实现细节

### 实战
- 用 Python 手写一个线程池(本 Day Q9)
- 用 Redis + Lua 实现一个分布式锁并写测试
- 用本地消息表模拟一个跨服务转账的最终一致流程

---

## 明日预告

**Day 34 — LLM 与 Transformer 基础**

后端知识是 Agent 的"骨架",LLM 是 Agent 的"大脑"。明天回到算法主线,系统过一遍:

- Transformer 架构(Self-Attention / Multi-Head / Positional Encoding / FFN / LayerNorm)
- 从 GPT 到 GPT-4 的演进(Decoder-only / Pretrain-SFT-RLHF / MoE)
- 关键概念:Token / Context Window / Temperature / Top-k / Top-p / KV Cache
- 推理优化:vLLM(PagedAttention)/ TensorRT-LLM / 量化(GPTQ/AWQ)/ 蒸馏
- 面试常考:为什么 Decoder-only 成为主流?Self-Attention 复杂度?RoPE 相比绝对位置编码的优势?

后端负责把 LLM 的能力**稳定地交付给用户**,算法负责让 LLM 的能力**本身更强**。两条腿走路,缺一不可。

---

> **今日小结**:后端八股是面试的"门槛题",不会直接拿分,但答得差会直接出局。Agent 方向面试官特别看重你对"LLM + 后端"结合的理解(Q10 就是核心)。建议把 Q9 的线程池代码默写到能 5 分钟内手写出来,Q10 的架构图能 3 分钟在白板画出。
