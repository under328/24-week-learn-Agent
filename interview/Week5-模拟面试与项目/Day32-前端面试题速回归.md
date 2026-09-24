# Day 32 — 前端面试题速回归

> **为什么要回归前端?**
>
> Agent 岗位面试中,「前端展示层」是高频考察区。面试官想看你能否把 Agent 的能力**可视化呈现**给用户,具体体现在:
>
> - **流式渲染**: SSE/WebSocket 流式 token 输出,如何平滑滚动、如何处理中断重连、如何避免重排抖动
> - **工具调用可视化**: Function Calling 的多步骤进度、参数预览、结果折叠、错误高亮
> - **多模态渲染**: Markdown / 代码高亮 / Mermaid 图 / 表格 / LaTeX / 图片 / 文件预览的混合渲染
> - **多轮对话状态管理**: 历史上下文、token 计数、上下文窗口裁剪的 UI 反馈
>
> 这些场景背后考察的全是前端基础:事件循环、异步并发、渲染流程、组件设计、性能优化。今天不是从零学,而是**帮你把已有知识快速激活**,把碎片串成体系。
>
> **学习目标**:
>
> 1. 1 天内回忆 HTML/CSS/JS/浏览器/网络/框架/性能的核心考点
> 2. 能手写 Promise.all、防抖节流、SSE 流式渲染组件
> 3. 能设计一个 Agent 前端展示层的系统架构
> 4. 形成可复用的「面试速记卡」,临场 30 秒内调出关键点

---

## 今日知识图谱

```
前端面试知识体系 (Day 32 速回归)
│
├── 1. HTML/CSS 基础
│   ├── 语义化标签 (header/nav/main/article/section/aside/footer)
│   ├── CSS 布局
│   │   ├── Flex (主轴/交叉轴, justify-content/align-items)
│   │   ├── Grid (行列模板, grid-template-areas)
│   │   ├── BFC (块级格式化上下文, 触发条件 & 应用)
│   │   └── 居中方案 (水平/垂直/水平垂直, 4种以上写法)
│   └── 响应式 (媒体查询 / rem-vw-vh / container query)
│
├── 2. JavaScript 核心
│   ├── 原型链 (proto / prototype / 原型继承)
│   ├── 闭包 (定义 / 应用 / 内存泄漏)
│   ├── this 指向 (默认/隐式/显式/new/箭头函数)
│   ├── 事件循环
│   │   ├── 浏览器: 调用栈 → 微任务 → 宏任务 → requestAnimationFrame → UI 渲染
│   │   └── Node.js: timer/poll/check/close 等阶段
│   └── ES6+ (let-const/箭头函数/解构/模板字符串/Class/Module/Symbol)
│
├── 3. JavaScript 异步
│   ├── Promise (状态机 / then链 / 错误处理)
│   ├── async/await (语法糖 / 错误捕获)
│   ├── 并发控制 (Promise.all / allSettled / race / any + 并发池)
│   └── 手写 (Promise.all / race / 并发限制器)
│
├── 4. 浏览器原理
│   ├── 渲染流程 (DOM → CSSOM → Render Tree → Layout → Paint → Composite)
│   ├── 重排 reflow & 重绘 repaint
│   ├── 关键渲染路径 CRP 优化
│   ├── 垃圾回收 (标记清除 / 分代回收 / V8 新生代老生代)
│   └── 进程/线程 (多进程架构 / 渲染线程 vs JS 线程互斥)
│
├── 5. 计算机网络
│   ├── HTTP/1.1 vs HTTP/2 vs HTTP/3 (队头阻塞/多路复用/QUIC)
│   ├── HTTPS (TLS 握手 / 证书链 / 对称+非对称)
│   ├── TCP 三次握手 & 四次挥手
│   ├── 跨域 (CORS / JSONP / 反向代理)
│   └── 缓存策略 (强缓存 Cache-Control/Expires + 协商缓存 ETag/Last-Modified)
│
├── 6. 框架 — React
│   ├── 虚拟 DOM & Diff (同层比较 / key / 三种策略)
│   ├── Hooks (useState/useEffect/useMemo/useCallback/useRef/useContext)
│   ├── Fiber 架构 (可中断 / 可恢复 / 时间分片)
│   ├── 并发模式 (Concurrent / Suspense / useTransition)
│   └── 状态管理 (Redux / Zustand / Jotai / Context)
│
├── 7. 框架 — Vue
│   ├── 响应式原理 (Vue2 Object.defineProperty vs Vue3 Proxy + Reflect)
│   ├── 生命周期 (Options vs Composition)
│   ├── 组合式 API (setup / ref / reactive / computed / watch)
│   ├── Diff 策略 (双端 Diff / 最长递增子序列)
│   └── React vs Vue 选型对比
│
├── 8. 性能优化
│   ├── 加载优化 (路由懒加载 / 预加载 / 代码分割 / Tree Shaking / CDN)
│   ├── 运行时优化 (防抖节流 / 虚拟列表 / Web Worker / requestIdleCallback)
│   ├── 监控 (Performance API / LCP-FID-CLS / Lighthouse / 埋点)
│   └── 图片优化 (WebP/AVIF / lazy / 响应式 srcset)
│
├── 9. TypeScript (Agent 岗加分)
│   ├── 类型体操 (Partial/Required/Pick/Omit/Record/ReturnType)
│   ├── 泛型 (函数泛型 / 类泛型 / 约束 extends)
│   └── 工具类型实战 (Agent 消息流类型设计)
│
└── 10. Agent 前端专题
    ├── SSE 流式渲染 (EventSource / ReadableStream / 自动滚动)
    ├── Markdown 渲染 (react-markdown / remark / rehype / 代码高亮)
    ├── 工具调用可视化 (步骤折叠 / 参数 diff / 状态机)
    ├── 多轮对话 (上下文裁剪 / 消息分页 / 撤销重发)
    └── 错误处理 (重试策略 / 降级 / 离线缓存)
```

---

## 面试题(共 10 道)

### Q1: HTML 语义化 + CSS 布局(Flex / Grid / BFC / 居中方案)

<details>
<summary><b>点击展开答案</b></summary>

**1. HTML 语义化的好处**

- 提升可访问性 (a11y):屏幕阅读器依据语义标签判断页面结构
- 提升 SEO:搜索引擎能理解内容权重 (article > div)
- 提升代码可读性,便于团队维护
- 默认样式合理 (button 有键盘焦点,form 有提交行为)

常用语义标签:
```html
<header> 顶部导航区
<nav> 导航
<main> 主内容 (页面唯一)
<article> 独立内容 (一篇博客/一条评论)
<section> 内容分块 (带标题)
<aside> 侧边栏/广告
<footer> 页脚
<figure> + <figcaption> 图文组合
<time> 时间
```

**2. Flex 布局速记**

```css
.container {
  display: flex;
  flex-direction: row | column | row-reverse | column-reverse;
  justify-content: flex-start | center | flex-end | space-between | space-around | space-evenly; /* 主轴 */
  align-items: stretch | flex-start | center | flex-end | baseline; /* 交叉轴 */
  flex-wrap: nowrap | wrap;
  gap: 8px;
}
.item {
  flex: 1;            /* = flex: 1 1 0%  等分剩余空间 */
  flex: 0 0 100px;    /* 固定 100px 不伸缩 */
  align-self: center; /* 单独对齐 */
}
```

记忆口诀:**主轴 justify,交叉 align**。

**3. Grid 布局速记**

```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);   /* 12 栅格 */
  grid-template-rows: auto;
  grid-template-areas:
    "header header header"
    "sidebar main main"
    "footer footer footer";
  gap: 16px;
}
.header { grid-area: header; }
```

Flex 是**一维**布局(一行或一列),Grid 是**二维**布局(行+列)。复杂网格优先 Grid,简单横向/纵向排列用 Flex。

**4. BFC(块级格式化上下文)**

**触发条件**(任一即可):
- `float` 不为 `none`
- `position` 为 `absolute` / `fixed`
- `display` 为 `inline-block` / `flex` / `grid` / `flow-root`
- `overflow` 不为 `visible` (常用 `overflow: hidden`)
- 根元素 `<html>`

**应用场景**:
1. **清除浮动**:父元素 `display: flow-root` 或 `overflow: hidden`,避免子元素浮动导致父高度塌陷
2. **避免 margin 重叠**:把元素放进 BFC 容器,margin 不再与外部重叠
3. **自适应两栏布局**:左浮动 + 右侧 `overflow: hidden` 形成新 BFC,不与浮动重叠

**5. 居中方案大全**(水平垂直居中)

```css
/* 方案 1: Flex (推荐) */
.parent { display: flex; justify-content: center; align-items: center; }

/* 方案 2: Grid */
.parent { display: grid; place-items: center; }

/* 方案 3: 绝对定位 + transform (未知尺寸) */
.child { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }

/* 方案 4: 绝对定位 + margin auto (已知尺寸) */
.child { position: absolute; inset: 0; margin: auto; width: 100px; height: 100px; }

/* 方案 5: table-cell (兼容老浏览器) */
.parent { display: table-cell; vertical-align: middle; text-align: center; }
```

**面试速答**: Flex `justify+align` 是首选;BFC 三大用途是清浮动/隔 margin/两栏布局。

</details>

---

### Q2: JavaScript 核心 — 原型链 / 闭包 / this / 事件循环(代码题)

<details>
<summary><b>点击展开答案</b></summary>

**1. 原型链**

```js
function Person(name) { this.name = name; }
Person.prototype.sayHi = function() { console.log(this.name); };

const p = new Person('Tom');
p.sayHi();          // 'Tom' —— 沿原型链找到 Person.prototype
p.toString();       // 沿原型链找到 Object.prototype.toString
```

链路:`p.__proto__ === Person.prototype` → `Person.prototype.__proto__ === Object.prototype` → `Object.prototype.__proto__ === null`。

**new 做了什么**:
1. 创建空对象 `{}`
2. 对象 `__proto__` 指向构造函数的 `prototype`
3. 构造函数 `this` 绑定到新对象并执行
4. 若返回值是对象则返回它,否则返回新对象

**2. 闭包**

函数访问其词法作用域外的变量,即使外层函数已返回,变量仍被保留。

```js
function counter() {
  let count = 0;
  return {
    inc: () => ++count,
    get: () => count,
  };
}
const c = counter();
c.inc(); c.inc();
console.log(c.get()); // 2
```

应用:模块化(私有变量)、防抖节流、柯里化、React Hooks(useState 闭包陷阱)。

**内存泄漏场景**: 闭包引用 DOM 元素,DOM 被移除但闭包仍持有引用 → 用 `WeakMap` / 显式置 `null`。

**3. this 指向五条规则**(优先级从高到低)

1. `new` 绑定:指向新创建的对象
2. 显式绑定 `fn.call(obj)` / `apply` / `bind`:指向传入的 obj
3. 隐式绑定 `obj.fn()`:指向调用方 obj
4. 默认绑定:非严格模式指向 `window`,严格模式 `undefined`
5. 箭头函数:继承外层函数的 `this`,无法被 `call/apply/bind` 改变

```js
const obj = {
  name: 'A',
  arrow: () => console.log(this.name),     // 外层 this (window)
  normal() { console.log(this.name); },    // obj
  delayed() {
    setTimeout(function() { console.log(this.name); }, 0);       // window
    setTimeout(() => console.log(this.name), 0);                  // obj
  },
};
```

**4. 事件循环代码题**(必考)

```js
console.log(1);                          // 同步
setTimeout(() => console.log(2), 0);     // 宏任务
Promise.resolve().then(() => console.log(3));  // 微任务
Promise.resolve().then(() => {
  console.log(4);
  Promise.resolve().then(() => console.log(5));  // 微任务套微任务
});
console.log(6);                          // 同步
```

**输出顺序**: `1 6 3 4 5 2`

**解析**:
- 同步代码先执行: `1, 6`
- 微任务队列在每次宏任务前清空: `3, 4`,执行 `4` 时又入队 `5`,继续清空 → `5`
- 宏任务: `2`

**事件循环模型**(浏览器):
```
1. 执行调用栈中的同步任务
2. 调用栈清空后,执行所有微任务 (Promise.then / queueMicrotask / MutationObserver)
3. 微任务清空后,执行 requestAnimationFrame 回调
4. 浏览器渲染 (UI 更新)
5. 执行一个宏任务 (setTimeout / setInterval / I/O / postMessage)
6. 回到第 2 步
```

**Node.js 阶段**(对比记忆):
`timers → pending callbacks → idle/prepare → poll → check(setImmediate) → close callbacks`,每个阶段切换前清空 `process.nextTick` 和微任务。

</details>

---

### Q3: JavaScript 异步 — Promise / async-await / 并发控制(手写)

<details>
<summary><b>点击展开答案</b></summary>

**1. Promise 状态机**

三种状态: `pending` → `fulfilled` / `rejected`,一旦确定不可逆。`then` 返回新 Promise,形成链式调用。

**错误处理**: `.then(null, handler)` 等价 `.catch(handler)`;`finally` 不接收值,继续向下传递。

**2. async/await 本质**

```js
async function f() {
  try {
    const a = await fetch('/api/a');
    const b = await fetch('/api/b');
    return [a, b];
  } catch (e) {
    console.error(e);
  }
}
```

- `await` 暂停函数执行,等待 Promise resolve,然后**把值「赋值」给左侧变量**并继续
- `async` 函数总是返回 Promise
- 错误用 `try/catch` 捕获,比 `.catch` 更接近同步写法
- **陷阱**: 串行 await 比并行慢,无依赖时用 `Promise.all`

```js
// 慢: 串行 2s
const a = await fetchA();  // 1s
const b = await fetchB();  // 1s

// 快: 并行 1s
const [a, b] = await Promise.all([fetchA(), fetchB()]);
```

**3. Promise 四兄弟**

| API | 行为 | 短路条件 |
|---|---|---|
| `Promise.all` | 全部 fulfilled 才 fulfilled | 任一 reject 立即 reject |
| `Promise.allSettled` | 等全部完成 | 不短路,返回 `{status, value/reason}[]` |
| `Promise.race` | 第一个完成(成功/失败)即返回 | 第一个 settle |
| `Promise.any` | 第一个 fulfilled 返回 | 全部 reject 才 reject (AggregateError) |

**4. 手写 Promise.all**

```js
Promise.myAll = function(promises) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(promises);
    const results = new Array(arr.length);
    let count = 0;
    if (arr.length === 0) return resolve([]);
    arr.forEach((p, i) => {
      Promise.resolve(p).then(
        val => {
          results[i] = val;          // 用 index 保序
          if (++count === arr.length) resolve(results);
        },
        reject                       // 任一失败立即 reject
      );
    });
  });
};
```

**5. 手写 Promise.race**

```js
Promise.myRace = function(promises) {
  return new Promise((resolve, reject) => {
    Array.from(promises).forEach(p => {
      Promise.resolve(p).then(resolve, reject);  // 第一个 settle 决定结果
    });
  });
};
```

**6. 并发限制器**(Agent 场景常用,如批量调用工具 API 控制并发)

```js
async function pool(tasks, limit) {
  const results = [];
  const executing = new Set();
  for (const task of tasks) {
    const p = Promise.resolve().then(task);
    results.push(p);
    executing.add(p);
    p.finally(() => executing.delete(p));
    if (executing.size >= limit) {
      await Promise.race(executing);   // 等最快的一个完成
    }
  }
  return Promise.all(results);
}

// 用法: 10 个任务,并发 3
const tasks = urls.map(url => () => fetch(url));
const data = await pool(tasks, 3);
```

**7. 错误处理最佳实践**

- 不要吞掉错误:`.catch(e => {})` 是反模式,至少 `console.error`
- 重试 + 指数退避:Agent 调用 LLM API 必备

```js
async function withRetry(fn, retries = 3, delay = 500) {
  for (let i = 0; i < retries; i++) {
    try { return await fn(); }
    catch (e) {
      if (i === retries - 1) throw e;
      await new Promise(r => setTimeout(r, delay * 2 ** i));
    }
  }
}
```

</details>

---

### Q4: 浏览器原理 — 渲染流程 / 重排重绘 / CRP 优化

<details>
<summary><b>点击展开答案</b></summary>

**1. 渲染流程六步**(必背)

```
HTML ──parse──> DOM Tree
                        └──> Render Tree ──> Layout (布局) ──> Paint (绘制) ──> Composite (合成)
CSS  ──parse──> CSSOM Tree
```

1. **解析 HTML 构建 DOM**:字节 → 字符 → 标签 → 节点 → DOM 树
2. **解析 CSS 构建 CSSOM**:CSS 选择器匹配,从右向左解析
3. **合成 Render Tree**:DOM + CSSOM 合并,忽略 `display: none` 的节点(`visibility: hidden` 保留)
4. **Layout 布局**:计算每个节点的几何信息(位置、大小)
5. **Paint 绘制**:将节点绘制为位图(像素),绘制顺序按 z-index 层叠
6. **Composite 合成**:GPU 将多个图层合成最终画面

**2. 重排 reflow vs 重绘 repaint**

| 类型 | 触发条件 | 代价 |
|---|---|---|
| 重排 | 几何属性变化:width/height/margin/padding/top/left/添加删除元素/窗口 resize | 高(重新 Layout + Paint + Composite) |
| 重绘 | 外观变化:color/background/visibility/box-shadow | 中(Paint + Composite) |
| 合成 | transform / opacity | 低(只 Composite,GPU 加速) |

**优化原则**:
- 用 `transform` 代替 `top/left` 做动画
- 用 `opacity` 代替 `visibility: hidden` 切换
- 批量修改 DOM:用 `DocumentFragment` 或先 `display: none` 再操作
- 避免逐条读取触发回流的属性(`offsetTop`、`clientWidth`),用 `getBoundingClientRect` 一次性读
- 现代浏览器有「布局批处理」机制,但强制同步布局(`读取后立即写入`)会破坏它

**3. 关键渲染路径 CRP 优化**

目标:缩短**首屏渲染时间** (First Paint / FCP)。

- **CSS 是阻塞渲染资源**:尽早 `<link>` 放 `<head>`,避免 `@import`(串行)
- **JS 是阻塞解析资源**:默认 `<script>` 阻塞 DOM 解析
  - `defer`:并行下载,DOM 解析后、`DOMContentLoaded` 前按顺序执行
  - `async`:并行下载,下载完立即执行(可能中断解析),顺序不确定
- **预加载**:`<link rel="preload" href="font.woff2" as="font" crossorigin>` 提前加载关键资源
- **预连接**:`<link rel="preconnect" href="https://cdn.example.com">` 提前完成 DNS/TLS
- **关键 CSS 内联**:首屏 CSS 直接写在 `<style>` 中,其余异步加载
- **减少关键资源数**:合并、压缩、HTTP/2 多路复用

```html
<head>
  <style>/* 首屏关键 CSS 内联 */</style>
  <link rel="preload" href="/main.js" as="script">
  <link rel="preconnect" href="https://api.openai.com">
</head>
<body>
  ...
  <script src="/main.js" defer></script>
</body>
```

**4. 浏览器多进程架构**(Chrome)

- Browser 进程:地址栏、书签、网络请求、文件存储
- Renderer 进程:每个 tab 一个(站点隔离后每个站点一个),负责 HTML/CSS/JS 解析与渲染
- GPU 进程:合成图层、WebGL
- Plugin 进程:Flash 等插件(已淘汰)
- Utility 进程:网络服务、音频服务等

**JS 单线程与渲染互斥**:JS 执行和 UI 渲染在同一个 Renderer 主线程,长时间 JS 任务会阻塞渲染 → 用 `requestIdleCallback` / Web Worker / 时间分片(`scheduler.yield`)让出主线程。

</details>

---

### Q5: 计算机网络 — HTTP/HTTPS/HTTP2/HTTP3 + TCP + 跨域 + 缓存

<details>
<summary><b>点击展开答案</b></summary>

**1. HTTP 版本对比**

| 版本 | 关键特性 | 痛点 |
|---|---|---|
| HTTP/1.0 | 每次请求新建 TCP 连接 | 连接开销大 |
| HTTP/1.1 | Keep-Alive 长连接 / 管道化 / Host 头 / 分块传输 | 队头阻塞 (HOL) — 一个慢请求阻塞后续 |
| HTTP/2 | 二进制分帧 / 多路复用 / 头部压缩 HPACK / 服务端推送 / 流优先级 | TCP 层队头阻塞(丢包阻塞所有流) |
| HTTP/3 | 基于 QUIC (UDP) / 0-RTT 建连 / 连接迁移 / 前向纠错 | 部署普及中 |

**HTTP/2 多路复用**:一个 TCP 连接上并行多个请求/响应,二进制帧交错传输,告别 1.1 的域名分片 hack。

**HTTP/3 QUIC 优势**:基于 UDP,在传输层解决队头阻塞;0-RTT 握手;连接迁移(WiFi 切 4G 不掉线)。

**2. HTTPS = HTTP + TLS**

- **对称加密** (AES):加密数据,快
- **非对称加密** (RSA/ECC):加密对称密钥,慢
- **证书链**:服务器证书 → 中间 CA → 根 CA,浏览器校验签名

**TLS 1.3 握手简化**:1-RTT(可选 0-RTT),比 TLS 1.2 的 2-RTT 更快。

**3. TCP 三次握手 & 四次挥手**

```
三次握手 (建立连接):
Client → SYN (seq=x)                  → Server
Client ← SYN+ACK (seq=y, ack=x+1)     ← Server
Client → ACK (ack=y+1)                → Server  (可携带数据)

四次挥手 (断开连接):
Client → FIN (seq=u)                  → Server
Client ← ACK (ack=u+1)                ← Server  (Server 还有数据可继续发)
Client ← FIN (seq=v)                  ← Server
Client → ACK (ack=v+1)                → Server  (进入 TIME_WAIT, 等 2MSL)
```

**为什么三次?** 防止已失效的连接请求到达 Server,造成资源浪费。
**为什么四次?** Server 收到 FIN 后可能还有数据未发完,所以 ACK 和 FIN 分开。
**TIME_WAIT 为什么 2MSL?** 确保最后 ACK 到达 Server,且让本连接的报文都从网络消失。

**4. 跨域解决方案**

同源策略:协议 + 域名 + 端口任一不同即跨域,限制 AJAX、Cookie、DOM 访问。

| 方案 | 原理 | 适用 |
|---|---|---|
| **CORS** | 服务端设 `Access-Control-Allow-Origin` | 主流,跨域 AJAX |
| **JSONP** | `<script src>` 不受同源限制,回调函数取数据 | 只能 GET,已淘汰 |
| **反向代理** | Nginx / Vite proxy 把跨域请求转同源 | 开发 & 部署 |
| **postMessage** | 窗口间通信 | iframe / 多窗口 |
| **WebSocket** | 不受同源策略限制 | 实时通信 |

**CORS 细节**:
- 简单请求:GET/HEAD/POST + 限定 header,直接发请求带 `Origin`,服务端返回 `Access-Control-Allow-Origin`
- 预检请求 OPTIONS:非简单请求先发 OPTIONS,带 `Access-Control-Request-Method/Headers`,服务端返回允许的方法、header、缓存时间
- 携带 Cookie:前端 `credentials: 'include'`,后端 `Access-Control-Allow-Credentials: true`,且 `Allow-Origin` 不能为 `*`

**5. 缓存策略**(高频)

```
浏览器请求 → 检查强缓存 → 命中? 直接用
                       ↓ 未命中
                  协商缓存 (带 If-Modified-Since / If-None-Match)
                       ↓
                  服务器返回 200 (有更新,带新资源) 或 304 (无更新,用本地)
```

| 类型 | 头字段 | 说明 |
|---|---|---|
| **强缓存** | `Cache-Control: max-age=3600` | 优先级高于 Expires,缓存期内不发请求 |
|  | `Expires: Wed, 23 Sep 2026 12:00:00 GMT` | HTTP/1.0,绝对时间,受本地时钟影响 |
| **协商缓存** | `ETag` / `If-None-Match` | 资源指纹 hash,优先级高 |
|  | `Last-Modified` / `If-Modified-Since` | 文件最后修改时间,精度秒级 |

**Cache-Control 常用值**:
- `public` / `private`:是否允许 CDN 等中间缓存
- `no-cache`:强制协商缓存(每次都问服务器)
- `no-store`:完全不缓存
- `immutable`:资源永不变,刷新也不协商(用于带 hash 文件名)
- `stale-while-revalidate`:后台异步刷新,先返回旧值

**最佳实践**:
- HTML: `no-cache` (要协商,确保拿到最新入口)
- 带 hash 的 JS/CSS: `max-age=31536000, immutable` (一年,文件名变就换)
- 用户数据 API: `no-store` (敏感)

</details>

---

### Q6: React 核心 — 虚拟 DOM / Diff / Hooks / Fiber / 并发模式(代码题)

<details>
<summary><b>点击展开答案</b></summary>

**1. 虚拟 DOM & Diff**

虚拟 DOM 是 JS 对象描述真实 DOM 的树结构。每次状态变更生成新 vDOM,与旧 vDOM 对比 (Diff),只把差异 patch 到真实 DOM。

**Diff 三大策略**(O(n) 复杂度):
1. **同层比较**:不跨层级移动
2. **类型不同直接替换**:标签不同(`div` → `span`)直接卸载重建
3. **key 标识同层唯一**:列表通过 key 复用节点,避免重排

**key 的作用**:列表更新时,React 用 key 判断哪些元素是新增/删除/移动。用 index 当 key 在「插入到头部」场景会导致后续所有节点重新渲染(因为 index 变了,React 认为是不同元素)。**必须用稳定唯一值**(id)。

**2. 核心 Hooks**

```tsx
// useState: 状态
const [count, setCount] = useState(0);
setCount(c => c + 1);  // 函数式更新,避免闭包陷阱

// useEffect: 副作用
useEffect(() => {
  const id = setInterval(() => console.log(count), 1000);
  return () => clearInterval(id);   // 清理函数
}, [count]);                          // 依赖数组,空数组只跑一次

// useMemo: 缓存计算结果
const expensive = useMemo(() => compute(data), [data]);

// useCallback: 缓存函数引用 (传给子组件避免重渲染)
const handleClick = useCallback(() => doSomething(id), [id]);

// useRef: 持久化可变值,不触发重渲染
const timerRef = useRef<number>();

// useContext: 跨层传值
const theme = useContext(ThemeContext);

// useReducer: 复杂状态
const [state, dispatch] = useReducer(reducer, initial);
```

**useEffect 闭包陷阱**:
```tsx
useEffect(() => {
  const t = setInterval(() => console.log(count), 1000);
  return () => clearInterval(t);
}, []);  // count 永远是 0! 依赖数组为空,count 闭包是初始值
```
解决:把 `count` 加进依赖,或用 `useRef` 持有最新值。

**3. Fiber 架构**

React 16 引入。把渲染工作拆成**可中断、可恢复**的 fiber 单元,每个 fiber 是一个组件节点。

- **可中断**:渲染过程中如果有更高优先级任务(用户输入),可以暂停
- **可恢复**:记录当前 fiber 进度,稍后从断点继续
- **时间分片**:每帧约 5ms 渲染时间,剩余交给浏览器响应交互

双缓冲机制: `current fiber tree` (当前显示) ↔ `workInProgress fiber tree` (正在构建),完成后切换 root 指针。

**4. 并发模式 Concurrent**

- `useTransition`:把状态更新标记为非紧急,让紧急更新(输入)优先
- `useDeferredValue`:延迟一个值的更新
- `Suspense`:配合 lazy / data fetching,「数据未就绪时显示 fallback」

```tsx
const [isPending, startTransition] = useTransition();
const onChange = e => {
  setQuery(e.target.value);              // 紧急:输入框立即更新
  startTransition(() => setResults(filter(e.target.value)));  // 非紧急:列表可延迟
};
```

**5. 代码题:用 Hooks 实现一个计数器 + 自动增加**

```tsx
function AutoCounter() {
  const [count, setCount] = useState(0);
  const [running, setRunning] = useState(true);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setCount(c => c + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setRunning(r => !r)}>
        {running ? '暂停' : '开始'}
      </button>
      <button onClick={() => setCount(0)}>重置</button>
    </div>
  );
}
```

**面试加分**: 提到 React 18 自动批处理 (automatic batching)、`useSyncExternalStore` 对接外部 store、Server Components。

</details>

---

### Q7: Vue 核心 — 响应式 / 生命周期 / 组合式 API / Diff / React 对比

<details>
<summary><b>点击展开答案</b></summary>

**1. 响应式原理对比**

**Vue 2 — `Object.defineProperty`**:
```js
Object.defineProperty(obj, key, {
  get() { /* 收集依赖 */ return val; },
  set(newVal) { val = newVal; /* 通知更新 */ },
});
```
痛点:无法监听属性新增/删除(需 `Vue.set`),无法监听数组下标修改(重写 7 个数组方法)。

**Vue 3 — `Proxy + Reflect`**:
```js
const proxy = new Proxy(target, {
  get(target, key, receiver) {
    track(target, key);               // 依赖收集
    return Reflect.get(target, key, receiver);
  },
  set(target, key, value, receiver) {
    const result = Reflect.set(target, key, value, receiver);
    trigger(target, key);             // 触发更新
    return result;
  },
});
```
优势:整体代理,新增/删除属性都能监听,数组下标直接可用,性能更好(惰性响应式,访问时才递归代理)。

**依赖收集流程**:`effect` (渲染/计算) 执行时读取响应式数据 → `track` 记录「该数据的订阅者」;数据变更 → `trigger` 重新运行所有订阅的 `effect`。

**2. 生命周期**(组合式 API)

```ts
setup() {
  onBeforeMount(() => {});
  onMounted(() => {});
  onBeforeUpdate(() => {});
  onUpdated(() => {});
  onBeforeUnmount(() => {});
  onUnmounted(() => {});
  onErrorCaptured(() => {});   // 捕获子组件错误
}
```

对应 Options API: `beforeCreate/created` → 直接写在 `setup` 函数体;`beforeMount/onBeforeMount`;`mounted/onMounted`;...

**3. 组合式 API 核心**

```ts
import { ref, reactive, computed, watch, watchEffect } from 'vue';

const count = ref(0);                  // 基本类型用 ref,需 .value
const state = reactive({ list: [] });  // 对象用 reactive
const double = computed(() => count.value * 2);
watch(count, (newVal, oldVal) => { /* 副作用 */ });
watchEffect(() => console.log(count.value));  // 自动追踪依赖
```

`ref` vs `reactive`:`ref` 包装任意值(基本类型也行),`reactive` 只代理对象。模板中 `ref` 自动解包,JS 中需 `.value`。

**4. Diff 策略对比**

- **React**:单向同层 Diff,靠 key 复用
- **Vue 2**:双端 Diff(头头、尾尾、头尾、尾尾四种比较 + key map)
- **Vue 3**:快速 Diff + 最长递增子序列 (LIS) 优化,最小化 DOM 移动

Vue 3 的 LIS 算法找出不需要移动的节点,只移动其余节点,移动次数接近最优。

**5. React vs Vue 选型**

| 维度 | React | Vue |
|---|---|---|
| 心智模型 | 函数式,UI = f(state),不可变 | 响应式,可变数据自动追踪 |
| 模板 | JSX (JS 写 UI,灵活) | 模板 (编译时优化,AI/低代码友好) |
| 状态 | 手动 `useState` / 状态库 | 自动响应式,开箱即用 |
| 上手 | JSX 学习曲线,生态选型多 | 模板语法清晰,约定大于配置 |
| 生态 | 大厂主流,Agent/低代码/可视化生态强 | 中后台模板丰富(Element Plus) |
| 编译优化 | 运行时 Diff 为主 | Vue 3 静态提升、PatchFlag 编译期优化 |
| 适合 | 复杂交互、跨端、大团队、定制需求多 | 中后台、表单密集、快速交付 |

**Agent 前端选型建议**: 如果做 Agent Playground / 可视化工具,React 生态(Next.js、shadcn/ui、Vercel AI SDK)更成熟;Vercel AI SDK、ai-sdk.dev 的 RSC 流式方案都是 React 优先。

</details>

---

### Q8: 前端性能优化 — 加载 / 运行时 / 监控

<details>
<summary><b>点击展开答案</b></summary>

**1. 加载优化**

| 手段 | 说明 |
|---|---|
| **路由懒加载** | `React.lazy` + `Suspense`,`import()` 动态导入,首屏只加载用到的 |
| **代码分割** | Webpack SplitChunks / Vite 自动分包,抽 vendor |
| **Tree Shaking** | ES Module 静态分析,删除未使用导出(需 ESM,禁 `export *`) |
| **预加载 preload** | 关键资源提前加载(字体、首屏 JS) |
| **预取 prefetch** | 空闲时加载下个可能用到的资源(下一页 JS) |
| **CDN 加速** | 静态资源放 CDN,边缘节点就近访问 |
| **Gzip / Brotli** | 压缩传输,Brotli 压缩率比 Gzip 高 15-20% |
| **HTTP/2 多路复用** | 单连接并行,消除域名分片 |
| **图片优化** | WebP/AVIF 格式、lazy loading、`srcset` 响应式图、CSS sprite |

```tsx
// 路由懒加载
const Chat = lazy(() => import('./Chat'));
<Suspense fallback={<Spinner />}><Chat /></Suspense>;
```

**2. 运行时优化**

| 手段 | 场景 |
|---|---|
| **防抖 debounce** | 搜索输入、resize,只在停止后执行一次 |
| **节流 throttle** | 滚动、mousemove,固定频率执行 |
| **虚拟列表** | 长列表只渲染可视区域 (react-window / vue-virtual-scroller) |
| **Web Worker** | CPU 密集计算搬到子线程,不阻塞主线程 |
| **requestAnimationFrame** | 动画对齐帧率,流畅 |
| **requestIdleCallback** | 空闲时执行低优先级任务 |
| **React.memo / useMemo / useCallback** | 减少不必要重渲染 |
| **CSS containment** | `contain: layout style paint` 隔离重排影响范围 |

**手写防抖节流**:

```js
// 防抖: 停止触发后执行
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// 节流: 固定频率执行
function throttle(fn, interval) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= interval) {
      last = now;
      fn.apply(this, args);
    }
  };
}
```

**虚拟列表核心思想**:
- 容器固定高度 + 内部 spacer 用 padding/transform 撑起总高度
- 监听 scrollTop,计算可视区间 `[start, end]`,只渲染这部分
- 上方留 buffer 防止滚动白屏

**3. 性能监控**

**核心 Web 指标 (Core Web Vitals)**:

| 指标 | 含义 | 优秀值 |
|---|---|---|
| **LCP** (Largest Contentful Paint) | 最大内容渲染时间 | < 2.5s |
| **INP** (Interaction to Next Paint) | 交互到下一帧(取代 FID) | < 200ms |
| **CLS** (Cumulative Layout Shift) | 累积布局偏移 | < 0.1 |

**Performance API**:
```js
// 采集关键节点
const [nav] = performance.getEntriesByType('navigation');
console.log({
  DNS: nav.domainLookupEnd - nav.domainLookupStart,
  TCP: nav.connectEnd - nav.connectStart,
  TTFB: nav.responseStart - nav.requestStart,
  FCP: performance.getEntriesByName('first-contentful-paint')[0].startTime,
  DOMReady: nav.domContentLoadedEventEnd - nav.startTime,
  Load: nav.loadEventEnd - nav.startTime,
});

// 观察 LCP
new PerformanceObserver(list => {
  for (const entry of list.getEntries()) console.log('LCP', entry.startTime);
}).observe({ type: 'largest-contentful-paint', buffered: true });
```

**上报方式**:`navigator.sendBeacon(url, data)` 在页面卸载时也能可靠发送(比 XHR 强)。

**4. Agent 前端特殊性能点**

- SSE 流式输出:每来一个 token 触发 setState,高频更新 → 用 `useRef` 缓冲 + `requestAnimationFrame` 批量 flush,避免每 token 一次 render
- 长对话历史:超过几千条消息时用虚拟列表,避免全量 DOM
- Markdown 渲染开销:长文本增量解析,或用 `useDeferredValue` 把渲染降级为低优先级
- 代码高亮:用 Web Worker 在子线程高亮,避免阻塞主线程

</details>

---

### Q9: 手撕代码 — 实现 Agent 对话前端组件(SSE 流式 + Markdown + 工具调用 + 代码高亮)

<details>
<summary><b>点击展开答案 + 完整代码</b></summary>

**需求拆解**:
1. 调用 `/api/chat` (SSE 接口),流式接收 token
2. 实时 Markdown 渲染(`react-markdown` + `remark-gfm` + `rehype-highlight`)
3. 工具调用展示:把 `tool_call` 事件渲染成可折叠的步骤卡片
4. 代码块语法高亮
5. 自动滚动到底部(用户上滚时不强制打断)
6. 错误重试 + 中断生成

**完整实现(React + TypeScript)**:

```tsx
// Chat.tsx
import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

type Role = 'user' | 'assistant' | 'tool';

interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  status: 'running' | 'done' | 'error';
  result?: unknown;
}

interface Message {
  id: string;
  role: Role;
  content: string;
  toolCalls?: ToolCall[];
  error?: string;
}

// 解析 SSE 流的辅助函数
async function* parseSSE(response: Response): AsyncGenerator<any> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';          // 留最后不完整的一行
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6);
      if (data === '[DONE]') return;
      try { yield JSON.parse(data); } catch { /* skip */ }
    }
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自动滚动: 仅当用户在底部时
  useEffect(() => {
    if (!autoScroll) return;
    const el = scrollRef.current;
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, autoScroll]);

  const onScroll = () => {
    const el = scrollRef.current!;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    setAutoScroll(atBottom);
  };

  const send = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: input };
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '' };
    setMessages(m => [...m, userMsg, assistantMsg]);
    setInput('');
    setLoading(true);
    setAutoScroll(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })) }),
        signal: ctrl.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      for await (const evt of parseSSE(res)) {
        setMessages(prev => prev.map(m => {
          if (m.id !== assistantMsg.id) return m;
          // 不同事件类型分别处理
          if (evt.type === 'token') {
            return { ...m, content: m.content + evt.value };
          }
          if (evt.type === 'tool_call') {
            const tc: ToolCall = { id: evt.id, name: evt.name, args: evt.args, status: 'running' };
            return { ...m, toolCalls: [...(m.toolCalls || []), tc] };
          }
          if (evt.type === 'tool_result') {
            return {
              ...m,
              toolCalls: m.toolCalls?.map(tc =>
                tc.id === evt.id ? { ...tc, status: evt.ok ? 'done' : 'error', result: evt.result } : tc
              ),
            };
          }
          if (evt.type === 'error') {
            return { ...m, error: evt.message };
          }
          return m;
        }));
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        setMessages(prev => prev.map(m => m.id === assistantMsg.id ? { ...m, content: m.content + '\n\n[已中断]' } : m));
      } else {
        setMessages(prev => prev.map(m => m.id === assistantMsg.id ? { ...m, error: e.message } : m));
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [input, loading, messages]);

  const stop = () => abortRef.current?.abort();

  const retry = () => {
    // 删除最后一条 assistant,重发上一条 user
    setMessages(prev => {
      const last = prev[prev.length - 1];
      if (last?.role !== 'assistant') return prev;
      const userInput = prev[prev.length - 2]?.content || '';
      setInput(userInput);
      return prev.slice(0, -2);
    });
  };

  return (
    <div className="chat">
      <div className="messages" ref={scrollRef} onScroll={onScroll}>
        {messages.map(m => (
          <div key={m.id} className={`msg msg-${m.role}`}>
            {m.role === 'user' && <p>{m.content}</p>}
            {m.role === 'assistant' && (
              <>
                {m.toolCalls?.map(tc => <ToolCallCard key={tc.id} call={tc} />)}
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                  {m.content}
                </ReactMarkdown>
                {m.error && <div className="error">⚠ {m.error} <button onClick={retry}>重试</button></div>}
              </>
            )}
          </div>
        ))}
      </div>
      <div className="input">
        <textarea value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="输入消息,Enter 发送" />
        {loading ? <button onClick={stop}>停止</button> : <button onClick={send}>发送</button>}
      </div>
    </div>
  );
}

// 工具调用卡片: 可折叠, 显示参数和结果
function ToolCallCard({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);
  const icon = call.status === 'running' ? '⏳' : call.status === 'done' ? '✅' : '❌';
  return (
    <details className="tool-call" open={open} onToggle={e => setOpen((e.target as details).open)}>
      <summary>{icon} 调用工具: {call.name}</summary>
      <pre>参数: {JSON.stringify(call.args, null, 2)}</pre>
      {call.result !== undefined && <pre>结果: {JSON.stringify(call.result, null, 2)}</pre>}
    </details>
  );
}
```

**关键点解析**(面试官追问):

1. **SSE 解析**: 用 `ReadableStream` + `TextDecoder` 增量解码,按 `\n` 分割,处理跨 chunk 的不完整行
2. **高频更新优化**: 上面的代码每个 token 都 setState,实际可加 `useRef` 缓冲 + `rAF` 批量 flush:
   ```ts
   const bufferRef = useRef('');
   // 收到 token 时: bufferRef.current += token; scheduleFlush();
   // rAF 回调里: setMessages(...); bufferRef.current = '';
   ```
3. **自动滚动**: 监听 `scrollTop` 判断用户是否在底部,避免强制打断用户上滚回看
4. **中断**: `AbortController` + `signal` 传给 fetch,后端也应该响应中断信号停止生成
5. **错误重试**: 保留 user 消息,删除 assistant,重新发送
6. **安全**: `react-markdown` 默认不执行 HTML,防 XSS;代码高亮用 `rehype-highlight`

</details>

---

### Q10: 系统设计 — Agent 前端展示层架构

<details>
<summary><b>点击展开答案 + 架构图</b></summary>

**需求**:
- 流式输出(SSE/WebSocket)
- 工具调用可视化(多步骤、参数、结果、状态)
- 多轮对话(上下文管理、历史分页)
- 多模态渲染(Markdown / 代码 / 表格 / 图片 / 文件 / 图表)
- 错误重试、降级、离线缓存
- 高并发场景(企业级多人使用)

**1. 整体架构**

```
┌─────────────────────────────────────────────────────────────┐
│                        浏览器 (Client)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  UI Layer (React + Next.js)                          │  │
│  │  ├── ChatView (消息列表, 虚拟列表)                   │  │
│  │  ├── MessageBubble (多模态渲染: MD/Code/Image/Chart) │  │
│  │  ├── ToolCallCard (工具调用步骤可视化)               │  │
│  │  ├── InputBar (输入 + 附件 + 快捷指令)               │  │
│  │  └── ContextPanel (Token 计数 + 上下文裁剪预览)      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State Layer                                         │  │
│  │  ├── Zustand Store (当前会话状态)                    │  │
│  │  ├── TanStack Query (历史会话列表, 服务端状态)        │  │
│  │  └── IndexedDB (离线缓存 + 草稿)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Streaming Layer                                     │  │
│  │  ├── SSEClient (EventSource / fetch+ReadableStream)  │  │
│  │  ├── EventParser (token/tool_call/tool_result/...)   │  │
│  │  ├── Buffer + rAF flush (高频更新合并)               │  │
│  │  └── Reconnect (指数退避 + 断点续传)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS / WSS
┌─────────────────────────┴───────────────────────────────────┐
│                    API Gateway (Nginx / 网关)                 │
│        鉴权 + 限流 + 熔断 + SSE 长连接 keep-alive            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                BFF / Agent Service (Node.js)                  │
│  ├── SessionManager (会话隔离 + 上下文窗口管理)              │
│  ├── AgentOrchestrator (LLM + Tools + RAG 编排)              │
│  ├── SSE Emitter (流式推送 token/tool 事件)                  │
│  ├── ToolRegistry (工具注册 + 沙箱执行)                       │
│  └── RateLimiter (per-user 令牌桶)                           │
└─────────────────────────────────────────────────────────────┘
```

**2. 核心数据模型**

```ts
interface Session {
  id: string;
  title: string;
  createdAt: number;
  messageCount: number;
  tokenCount: number;          // 用于上下文窗口裁剪提示
}

interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  parts?: MessagePart[];       // 多模态: 文本/图片/文件/图表混合
  toolCalls?: ToolCall[];
  status: 'streaming' | 'done' | 'error' | 'aborted';
  createdAt: number;
}

interface MessagePart {
  type: 'text' | 'image' | 'file' | 'chart' | 'table' | 'code';
  data: unknown;               // 各类型结构不同
}

interface ToolCall {
  id: string;
  name: string;
  args: unknown;
  status: 'pending' | 'running' | 'success' | 'error';
  result?: unknown;
  startedAt: number;
  endedAt?: number;
  error?: string;
}
```

**3. 流式协议设计(SSE 事件格式)**

```
event: token
data: {"value":"你"}

event: token
data: {"value":"好"}

event: tool_call
data: {"id":"tc_1","name":"search_web","args":{"query":"天气"}}

event: tool_result
data: {"id":"tc_1","ok":true,"result":{"temp":25}}

event: done
data: [DONE]
```

**为什么 SSE 而不是 WebSocket?**
- SSE 是单向服务端推送,语义匹配(不需要客户端实时发消息)
- 基于 HTTP,走标准 CDN/网关,自动重连,调试简单
- WebSocket 适合双向(协作编辑、游戏),Agent 场景过重
- 但若需要客户端随时中断/工具补充参数,WebSocket 更灵活

**4. 关键设计点**

**A. 流式渲染性能**
- 每个 token 触发 setState 会卡顿:用 `useRef` 缓冲 + `requestAnimationFrame` 批量 flush
- 长消息 Markdown 解析开销大:用 `useDeferredValue` 让渲染降级为低优先级,不阻塞输入
- 代码高亮放 Web Worker,避免阻塞主线程

**B. 多轮对话上下文**
- 前端展示历史 + token 计数条
- 后端负责上下文窗口裁剪(滑动窗口 / 摘要压缩),前端只透出「已裁剪」标识
- 长会话分页加载,IndexedDB 缓存历史,滚动到顶部触发加载更多

**C. 工具调用可视化**
- 用状态机: `pending → running → success | error`
- 可折叠卡片:展开看参数、结果、耗时
- 并行工具调用:横向并排卡片;串行调用:纵向时间线
- 工具链路:复杂 Agent 多步推理时,渲染成树形/有向图(Mermaid 或自绘 SVG)

**D. 多模态渲染**
- `MessagePart[]` 数组按顺序渲染,每种类型对应一个组件
- Markdown 内嵌图表:用 `rehype-mermaid` 在浏览器端渲染 Mermaid
- 图片懒加载 + 点击放大(lightbox)
- 文件预览:PDF 用 `<embed>`,代码用 Monaco Editor

**E. 错误处理 & 重试**
- 网络中断:指数退避重连,带 `Last-Event-ID` 续传
- LLM 返回错误:展示错误卡片 + 重试按钮(保留原 prompt)
- 工具执行失败:卡片标红 + 「重试此工具」按钮(后端 Agent Orchestrator 单独重跑)
- 离线:IndexedDB 缓存草稿,上线自动同步

**F. 安全**
- Markdown 默认不渲染 HTML(`react-markdown` 安全)
- 代码块禁用 `dangerouslySetInnerHTML`
- 用户上传文件扫描病毒、限制类型大小
- SSE 接口鉴权(JWT in header,EventSource 不支持自定义 header 时用 `?token=` + 短时效)

**5. 可扩展性**

- **多 Agent 切换**:Store 支持 multiple sessions,每个 session 绑定一个 Agent 配置
- **插件化渲染**:MessagePart 类型注册机制,新类型通过插件注册组件
- **主题切换**:CSS Variables + Tailwind,支持暗黑/品牌色
- **国际化**:i18next,消息内容不翻译(原文展示),UI 文案翻译

**6. 监控**

- 前端埋点:首屏加载时间、首 token 延迟(TTFT)、完整响应时间、工具调用成功率
- Sentry 捕获异常
- 用户反馈(👍👎)上报,用于 RLHF 数据收集

**面试加分**:
- 提到 Server Components + Streaming SSR(Next.js App Router)做首屏优化
- 提到 Vercel AI SDK 的 `useChat` hook 已经封装了大部分 SSE 逻辑
- 提到 IndexedDB 用 `Dexie.js` 简化,或 `idb-keyval` 轻量方案
- 提到 Web Worker 用 `comlink` 简化通信

</details>

---

## 核心知识回顾表

| 知识点 | 核心内容 | 面试频率 |
|---|---|---|
| HTML 语义化 | header/nav/main/article/section/footer,提升 a11y/SEO/可读性 | ★★★ |
| Flex/Grid | 主轴 justify、交叉 align;Grid 二维模板;Flex 一维 | ★★★★★ |
| BFC | 触发:float/position/display/overflow;用途:清浮动/隔 margin/两栏 | ★★★★ |
| 居中方案 | Flex、Grid place-items、绝对定位+transform、margin auto | ★★★★ |
| 原型链 | `__proto__` → `prototype` → `Object.prototype` → null;new 四步 | ★★★★ |
| 闭包 | 函数访问词法作用域外变量;应用:模块/防抖/Hooks;注意内存泄漏 | ★★★★★ |
| this 指向 | new > 显式 > 隐式 > 默认 > 箭头;箭头继承外层 | ★★★★★ |
| 事件循环 | 同步 → 微任务 → rAF → 渲染 → 宏任务;微任务清空才进宏任务 | ★★★★★ |
| Promise | 三态不可逆;all/allSettled/race/any 短路逻辑 | ★★★★★ |
| async/await | 语法糖,await 暂停函数;并行用 Promise.all;try/catch | ★★★★★ |
| 并发控制 | 限制并发池模式;`Promise.race(executing)` 释放槽位 | ★★★★ |
| 渲染流程 | DOM → CSSOM → Render Tree → Layout → Paint → Composite | ★★★★★ |
| 重排重绘 | 几何变化重排,外观变化重绘;transform/opacity 只触发合成 | ★★★★ |
| CRP 优化 | CSS 阻塞渲染,JS 阻塞解析;defer/async;preload/preconnect | ★★★ |
| HTTP/1.1 vs 2 vs 3 | 1.1 队头阻塞;2 多路复用+HPACK;3 QUIC+0-RTT | ★★★★ |
| HTTPS/TLS | 对称加密数据 + 非对称加密密钥;证书链;TLS1.3 1-RTT | ★★★ |
| TCP 三次握手 | SYN → SYN+ACK → ACK;防失效连接请求 | ★★★★ |
| TCP 四次挥手 | FIN → ACK → FIN → ACK;TIME_WAIT 2MSL | ★★★ |
| CORS | 简单请求 vs 预检 OPTIONS;Allow-Origin/Credentials/Headers | ★★★★★ |
| 缓存策略 | 强缓存(Cache-Control max-age)+ 协商(ETag/If-None-Match) | ★★★★★ |
| 虚拟 DOM/Diff | 同层比较、类型不同替换、key 复用;index 当 key 是反模式 | ★★★★ |
| React Hooks | useState/useEffect/useMemo/useCallback/useRef;闭包陷阱 | ★★★★★ |
| Fiber | 可中断可恢复;双缓冲;时间分片 5ms | ★★★ |
| 并发模式 | useTransition/useDeferredValue/Suspense;紧急 vs 非紧急更新 | ★★★ |
| Vue3 响应式 | Proxy+Reflect 替代 defineProperty;track/trigger | ★★★★ |
| Vue vs React | 响应式 vs 函数式;模板 vs JSX;编译优化 vs 运行时 Diff | ★★★ |
| 加载优化 | 路由懒加载/Tree Shaking/CDN/preload/Brotli | ★★★★ |
| 防抖节流 | debounce 停止后执行;throttle 固定频率;手写 | ★★★★★ |
| 虚拟列表 | 只渲染可视区+buffer;容器+spacer;scrollTop 计算 | ★★★★ |
| Web Vitals | LCP<2.5s / INP<200ms / CLS<0.1;PerformanceObserver | ★★★★ |
| SSE 流式 | EventSource / fetch+ReadableStream;rAF 批量 flush | ★★★★ (Agent 岗) |
| 工具调用可视化 | 状态机 pending→running→success/error;可折叠卡片 | ★★★ (Agent 岗) |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────────────┐
│                  前端核心速记卡 (Day 32)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [CSS]   Flex 主轴 justify 交叉 align | Grid 二维 place-items       │
│          BFC: float/pos/display/overflow → 清浮动/隔margin/两栏     │
│          居中: Flex > Grid > transform > margin auto                │
│                                                                     │
│  [JS]    原型链: __proto__ → prototype → Object.prototype → null    │
│          闭包: 函数访问词法作用域外变量, 注意泄漏                    │
│          this: new > 显式 > 隐式 > 默认 > 箭头(继承外层)             │
│          事件循环: 同步 → 微 → rAF → 渲染 → 宏                       │
│                                                                     │
│  [异步]  Promise 三态不可逆; all 全成 / allSettled 全完 /            │
│          race 第一个 / any 第一个成功; async/await 语法糖            │
│          并发池: Promise.race(executing) 释放槽位                    │
│                                                                     │
│  [浏览器] 渲染: DOM→CSSOM→RenderTree→Layout→Paint→Composite         │
│          重排(几何) > 重绘(外观) > 合成(transform/opacity)           │
│          CRP: CSS 阻塞渲染, JS 阻塞解析; defer 顺序 / async 乱序    │
│                                                                     │
│  [网络]  H2 多路复用 | H3 QUIC/0-RTT | TLS 对称+非对称              │
│          TCP 3次握手防失效, 4次挥手 TIME_WAIT 2MSL                  │
│          CORS: 简单/预检 OPTIONS; Allow-Origin+Credentials          │
│          缓存: 强(Cache-Control max-age) > 协商(ETag/If-None-Match) │
│                                                                     │
│  [React] Diff: 同层 + key 复用; Hooks: state/effect/memo/callback   │
│          Fiber: 可中断可恢复 双缓冲; 并发: useTransition/Suspense    │
│          闭包陷阱: 空依赖数组闭包旧值, 用 ref 持有最新                │
│                                                                     │
│  [Vue]   Vue3 Proxy+Reflect track/trigger; setup/ref/reactive       │
│          Vue3 Diff: 快速 + 最长递增子序列                            │
│          vs React: 响应式 vs 函数式, 模板 vs JSX                    │
│                                                                     │
│  [性能]  防抖(停止后)/节流(固定频率); 虚拟列表(可视区+buffer)        │
│          Web Worker 重活; rAF 动画; LCP<2.5s INP<200ms CLS<0.1      │
│          Tree Shaking 需 ESM; Brotli 优于 Gzip; preload 关键资源    │
│                                                                     │
│  [Agent] SSE: fetch+ReadableStream + rAF 批量 flush                 │
│          工具调用: 状态机 + 可折叠卡片 + 参数/结果 diff             │
│          自动滚动: scrollTop 判断在底部才滚, 不打断用户              │
│          中断: AbortController + signal; 错误: 指数退避重试         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **`flex: 1` 不等于 `flex: 1 1 auto`**
   `flex: 1` 实际是 `1 1 0%`,基础尺寸为 0,完全按比例分配;`flex: 1 1 auto` 基础尺寸是 `auto`(元素自身大小),行为不同。容易导致 Flex 项不等分。

2. **`==` 与 `===` 的坑**
   `[] == false` 是 `true`(都转 0);`null == undefined` 是 `true` 但 `null == 0` 是 `false`。面试一律用 `===`,除非明确判断 `null/undefined` 用 `== null`。

3. **事件循环里 `setTimeout` vs `Promise.then` 顺序**
   `Promise.then` 是微任务,在 `setTimeout`(宏任务)之前执行。常见错误:以为 `setTimeout(0)` 比 `Promise` 快。正确顺序是同步 → 微任务 → 宏任务。

4. **`useEffect` 空依赖数组闭包陷阱**
   `useEffect(() => { setInterval(() => console.log(count), 1000) }, [])` 中 `count` 永远是初始值。解决:加入依赖数组,或用 `useRef` 持有最新值,或用函数式更新。

5. **`key=index` 在列表头部插入时性能灾难**
   React 用 key 判断节点是否复用。用 index 当 key,在头部插入新元素后,后续所有 index 变化,React 认为它们是不同元素,触发全量重渲染。必须用稳定唯一 id。

6. **`overflow: hidden` 不等于清浮动最佳实践**
   `overflow: hidden` 会裁剪超出内容(如下拉菜单、tooltip)。推荐用 `display: flow-root`(无副作用)或 clearfix 伪元素。

7. **HTTP 缓存 `no-cache` 不是不缓存**
   `no-cache` 是「每次使用前必须向服务器验证」(协商缓存);`no-store` 才是「完全不缓存」。混淆会导致资源重复下载或拿不到最新版本。

8. **CORS 携带 Cookie 时 `Allow-Origin` 不能为 `*`**
   必须 `Access-Control-Allow-Origin: https://具体域名`,且 `Access-Control-Allow-Credentials: true`,前端 `fetch(url, { credentials: 'include' })`。否则 Cookie 不发。

9. **重排重绘的「批量批处理」会被强制同步布局破坏**
   `element.offsetWidth` 等读取几何属性会强制浏览器立即 Layout。如果在写入样式后立即读取,会触发「强制同步布局」(layout thrashing),性能极差。应一次性读取所有需要的值再写入。

10. **SSE 流式渲染每 token setState 卡顿**
    每个 token 一次 `setState` 在长输出时会导致主线程被 render 占满。正确做法:`useRef` 缓冲 token,`requestAnimationFrame` 每帧只 flush 一次到 state;或用 `useDeferredValue` 把渲染降级为低优先级。这是 Agent 前端最常翻车点。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 我能在 30 秒内说出 BFC 的触发条件和 3 个应用场景
- [ ] 我能默写出事件循环的执行顺序(同步 → 微 → rAF → 渲染 → 宏)
- [ ] 我能解释 `Promise.all` vs `allSettled` vs `race` vs `any` 的差异和短路逻辑
- [ ] 我能画出浏览器渲染的 6 个步骤(DOM → CSSOM → Render Tree → Layout → Paint → Composite)
- [ ] 我能区分重排、重绘、合成,并说出各自触发的 CSS 属性
- [ ] 我能说出 HTTP/1.1、HTTP/2、HTTP/3 各自的核心特性和痛点
- [ ] 我能解释 TCP 三次握手为什么是三次,四次挥手为什么是四次
- [ ] 我能说出强缓存和协商缓存的头字段,以及 `no-cache` vs `no-store` 的区别
- [ ] 我能说出 React Fiber 的可中断可恢复机制和双缓冲
- [ ] 我能对比 Vue3 Proxy 响应式 vs Vue2 defineProperty 的优势

### 代码题(3 个)

- [ ] 我能 5 分钟内手写 `Promise.all`(保序、短路、空数组处理)
- [ ] 我能 5 分钟内手写防抖 `debounce` 和节流 `throttle`
- [ ] 我能手写一个 SSE 流式渲染组件的核心逻辑(fetch + ReadableStream + setState + AbortController)

### 系统设计题(2 个)

- [ ] 我能画出 Agent 前端展示层的整体架构图(UI / State / Streaming 三层 + BFF)
- [ ] 我能讲清流式渲染性能优化(token 缓冲 + rAF flush)、工具调用可视化(状态机)、错误重试(指数退避 + 断点续传)三个关键设计点

---

## 延伸阅读

### 官方文档
- [MDN Web Docs](https://developer.mozilla.org/) — 权威参考,面试前查 API 必备
- [React 官方文档](https://react.dev/) — 新文档带 Hooks、并发模式、Server Components
- [Vue 3 官方文档](https://vuejs.org/) — 组合式 API、响应式原理
- [web.dev](https://web.dev/) — Google 性能优化权威,Core Web Vitals 指标定义

### 经典文章
- [浏览器渲染原理](https://developers.google.com/web/fundamentals/performance/critical-rendering-path) — CRP 详解
- [Event Loop 规范](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) — HTML 规范原文
- [Flexbox 完整指南](https://css-tricks.com/snippets/css/a-guide-to-flexbox/) — CSS-Tricks 经典
- [Grid 完整指南](https://css-tricks.com/snippets/css/complete-guide-grid/) — CSS-Tricks 经典

### Agent 前端专题
- [Vercel AI SDK 文档](https://sdk.vercel.ai/docs) — `useChat` hook,封装了 SSE 流式逻辑
- [react-markdown](https://github.com/remarkjs/react-markdown) — Markdown 渲染,支持插件
- [shadcn/ui](https://ui.shadcn.com/) — Agent Playground 常用组件库
- [LangChain.js](https://js.langchain.com/) — 前端可直接调用,带流式回调

### 性能监控
- [web-vitals 库](https://github.com/GoogleChrome/web-vitals) — 一行代码采集 LCP/INP/CLS
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) — 性能审计工具
- [Chrome DevTools Performance 面板](https://developer.chrome.com/docs/devtools/performance/) — 火焰图分析

### 面试题库
- [前端面试题宝典](https://fe.ecool.fun/) — 中文题库,分类齐全
- [Big Frontend Dev Questions](https://bigfrontend.dev/) — 英文,代码题为主
- [JavaScript Questions](https://github.com/lydiahallie/javascript-questions) — 100+ JS 怪题,陷阱题来源

---

## 明日预告

**Day 33 — 后端常见面试题速回归**

明天我们会快速回归后端核心知识,因为 Agent 岗位面试同样会考察后端能力(Agent 服务编排、API 设计、并发处理、数据存储):

- **语言基础**: Python(异步 asyncio / GIL / 装饰器 / 上下文管理器) vs Node.js(事件循环 / Stream) vs Go(goroutine / channel / GMP)
- **Web 框架**: FastAPI / Express / Gin,RESTful 设计,中间件,鉴权
- **数据库**: MySQL(索引/事务/隔离级别/锁)、PostgreSQL、Redis(数据结构/持久化/缓存策略)、MongoDB
- **消息队列**: Kafka / RabbitMQ / Redis Stream,应用场景
- **微服务**: 服务注册发现、配置中心、链路追踪、熔断限流
- **Agent 后端专题**: LLM API 调用、Function Calling 编排、向量数据库(Milvus/Pinecone/Chroma)、RAG 检索流程、Agent 编排框架(LangGraph / CrewAI / AutoGen)
- **系统设计**: 设计一个 Agent 服务端(多租户、会话隔离、工具沙箱、限流、监控)

后端是 Agent 的「身体」,前端是 Agent 的「脸」,两者结合才能交付完整产品。我们明天见。

---

> **今日总结**: 前端面试的核心是「**事件循环 + 渲染流程 + 框架原理 + 网络 + 性能**」五大块,Agent 前端在此基础上多了「**流式渲染 + 工具调用可视化 + 多模态**」三个专题。把速记卡背熟,把 Q9 的 SSE 组件代码手写过一遍,Day 32 就算达标。
