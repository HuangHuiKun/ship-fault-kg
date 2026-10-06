# 本机 Neo4j 连接与默认端口调整说明

调整日期：2026-10-05。目标实例：Neo4j Desktop 2 中的 `ShipFaultKG`；知识图谱数据库：`shipfaultkg`。

## 以后怎样打开

1. 打开 Neo4j Desktop 2 → Local instances。
2. 找到 **ShipFaultKG**，如果是 STOPPED，点击 **一次 Start**。如果已经是 RUNNING，不再启动。
3. 等待 RUNNING。日志中此实例过去的一次启动约耗时 46 秒；这是历史观察，不代表每次固定需要 46 秒。启动过程中不要反复点 Start，也不要同时运行命令行的 `neo4j console`。
4. 打开 [Neo4j Browser](http://localhost:7474/browser/)。如 localhost 解析异常，用 [127.0.0.1 地址](http://127.0.0.1:7474/browser/)。
5. 登录时使用以下设置：

| 项目 | 设置 |
| --- | --- |
| 浏览器网页 | `http://localhost:7474/browser/` |
| 数据库协议 | 本机单实例可用 `bolt://` |
| 数据库地址 | `127.0.0.1:7687` |
| 用户名 | `neo4j` |
| 密码 | 使用您当前密码；本文和检测脚本不保存密码 |
| 数据库 | 登录后选 `shipfaultkg`，或运行 `:use shipfaultkg` |

**7474 是网页端口，7687 是数据库连接端口。密码框里的连接地址不能填 7474。** `neo4j://127.0.0.1:7687` 也是有效的路由连接方式；本机单实例使用 `bolt://` 可以减少路由环节。

不要继续使用旧的 `7475` 网页或 `7690` 数据库连接。7474 和 7475 属于不同的网页来源，旧页面保存的连接信息不会自动迁移。

## 这次查到了什么

- 检查时，7474、7475、7687、7690 均没有监听，目标 Neo4j Java 进程也未运行；日志末尾是正常停止记录。因此，当前“localhost 拒绝连接”不是密码问题，而是服务器未启动或地址不对。
- 原配置实际使用 HTTP 7475、Bolt 7690；使用默认地址会访问不到这份实例。
- 2026-10-05 日志中明确出现过 `store_lock` 被其他进程占用：同一份数据库被重复启动，第二份进程启动失败。**不能通过删除锁文件解决**，应避免重复启动并正常停止旧进程。
- 历史日志包含启动成功和用户登录成功。检查范围内未找到明确的错误密码记录，因此不能把此前所有“连接失败”都归因于密码错误。旧连接信息、服务未就绪或实例冲突均需要区分。
- 本机还有旧的 Windows `neo4j` 服务，指向 `D:\neo4j\neo4j-community-5.26.30`；检查时它处于 **Stopped / Disabled**，本次没有改动或启动它。不要让它与 Desktop 中的 ShipFaultKG 同时争用默认端口。

## 已做的修改

配置文件位于：

`C:\Users\18270\.Neo4jDesktop2\Data\dbmss\dbms-956da0b3-4eec-4a04-aa01-484899f94108\conf\neo4j.conf`

```properties
server.default_listen_address=127.0.0.1
server.default_advertised_address=127.0.0.1
server.bolt.listen_address=:7687
server.bolt.advertised_address=:7687
server.http.listen_address=:7474
server.http.advertised_address=:7474
```

同时修改监听和对外告知地址，避免页面仍指引客户端连接旧端口。只监听本机回环地址，不开放给局域网；密码认证保持开启，没有为了连接方便而关闭安全校验。

### Desktop 2 地址重复问题的修正

本机安装版本的 `getConnectionUri` 将 `defaultAdvertisedAddress` 与 `boltListenAddress` 直接拼接。因此，虽然 Neo4j 服务器接受完整的 `127.0.0.1:7687`，将它写入 `server.bolt.listen_address` 会导致 Desktop 生成 `neo4j://127.0.0.1127.0.0.1:7687`。上一轮修改存在这项兼容性遗漏；现已改为上面的“默认地址 + 仅端口”写法。

正确拼接结果是 `neo4j://` + `127.0.0.1` + `:7687`，即 `neo4j://127.0.0.1:7687`。监听范围仍为本机，端口、密码和数据库均不变。如果已打开的连接弹窗还显示旧地址，关闭后重新打开，并将旧地址替换为正确地址。必要时在 Desktop 中正常 Stop / Start 一次，使运行中的服务也重新读取配置；不要启动第二份命令行进程。

本次修正前配置另备份在 `output/neo4j_connection_repair_20261005/neo4j.conf.before_desktop_url_fix`，用于追溯；该版本有 Desktop URL 拼接问题，不建议日常恢复使用。

- `neo4j-admin server validate-config` 检查通过，配置文件和两份日志配置均无问题。
- Desktop URL 修正后的只读核验：7474 网页返回 HTTP 200，服务器告知正确的 `bolt://127.0.0.1:7687` 与 `neo4j://127.0.0.1:7687`；现有密码连续 5 次认证查询均成功，`shipfaultkg` 为 online。核验得到 500 个活动节点、1201 条活动关系、15 个活动测点和55个归档测点。检测记录见 `output/neo4j_connection_repair_20261005/login_check_after_desktop_fix.json`，不含密码。
- 实际 Neo4j Browser 登录也已通过：页面显示 `connected`、实例 `neo4j://127.0.0.1:7687`，选中 `shipfaultkg` 后查询返回 500 / 1201。截图为 `output/neo4j_connection_repair_20261005/browser_connected.png`。本次无法直接操作 Desktop 原生窗口；Desktop URI 的核验依据其本机安装代码与新配置，网页连接核验则是实际操作结果。
- `ship_fault_kg/import_neo4j.py` 的默认 HTTP 地址同步改为 `http://127.0.0.1:7474`，环境变量 `NEO4J_URL` 仍可显式覆盖。
- **没有重建数据库、重新导入图谱、删节点或重置密码。**
- 原配置备份：[neo4j.conf.before](output/neo4j_connection_repair_20261005/neo4j.conf.before)。需要恢复时先停止实例，再将备份复制回上述配置文件，并重新启动；本次备份只包含配置，不是数据库数据备份。

## 出现问题时怎样判断

| 表现 | 优先检查 | 不要做什么 |
| --- | --- | --- |
| 网页“拒绝连接” | ShipFaultKG 是否 RUNNING、网页是否 7474 | 不要反复修改密码 |
| 网页能开，连接失败 | Bolt 是否 7687、实例是否完全启动、账号信息 | 不要把网页端口当数据库端口 |
| 明确提示 Unauthorized | 用户名、密码、是否连到正确实例 | 不要关闭认证或连续重试触发限流 |
| Start 报锁文件冲突 | 是否有另一进程启动同一数据目录 | 不要删 store_lock 或数据目录 |
| Start 报端口被占用 | 是否启动了旧 Windows 服务或另一实例 | 不要直接终止未知 Java 进程 |

## 快速检测工具

在项目目录的 PowerShell 中运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ship_fault_kg\check_neo4j_ready.ps1
```

这是只读检查，不会再启动一个 Neo4j 进程。要检查密码及图谱查询，可以使用项目 Python 环境：

```powershell
python .\ship_fault_kg\check_neo4j_connection.py
```

密码由终端隐藏输入，不放在命令行参数、代码或检测结果中。脚本检查 HTTP 服务、Bolt 协议握手，并连续执行 5 次只读的认证查询。Bolt 握手测试不等于完整的 Bolt 密码认证；浏览器实际登录另行核验。

## 正常结束

在 Desktop 中点击 ShipFaultKG 的 **Stop**，等待 STOPPED 后退出 Desktop。关网页并不等于停止数据库；停止数据库后仅重新打开网页也不会自动启动数据库。

## 官方参考

- [网络连接器、默认端口与监听/告知地址](https://neo4j.com/docs/operations-manual/current/configuration/connectors/)
- [Desktop 实例管理及启动/停止](https://neo4j.com/docs/desktop/current/operations/instance-management/)
