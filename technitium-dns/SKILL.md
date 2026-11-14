---
name: technitium-dns
description: 管理 Technitium DNS Server 实例的 API 客户端。包括 zone/record 管理、缓存操作、允许/阻止列表、DNS 设置、日志查询、用户管理等。
metadata:
  hermes:
    category: devops
    tags: [dns, api-client, devops, network]
    related_skills: [hermes-agent-skill-authoring]
---

# Technitium DNS Server 管理 Skill

通过 HTTP API 管理一个或多个 [Technitium DNS Server](https://github.com/TechnitiumSoftware/DnsServer) 实例。该 skill 提供了一个 Python CLI 脚本，封装了完整的 API。

> 官方 API 文档: https://github.com/TechnitiumSoftware/DnsServer/blob/master/APIDOCS.md

## 前置条件

- Technitium DNS Server v15.0+ (推荐)
- API 端口默认 `5380` (HTTP) 或 `53443` (HTTPS)
- 需要管理员账号或 API Token

## 快速开始
## 配置

通过 Hermes config 设置（推荐，优先读取）：

```bash
hermes config set tds.base_url http://192.168.1.100:5380
hermes config set tds.token your-api-token
```

也可以通过环境变量（fallback）：

```bash
export TDS_BASE="http://192.168.1.100:5380"
export TDS_TOKEN="your-api-token"
```

优先级: **Hermes config > 环境变量 > 默认值** (`http://localhost:5380`)

### 首次获取 Token

```bash
# 登录获取 session token
python3 scripts/api_client.py login admin your-password
```

输出示例：
```
932b2a...98e9
{
  "version": "15.0",
  ...
}
```

第一行是 token。建议为自动化脚本创建 API Token（永久有效）：

```bash
# 设置 base URL 和 session token
hermes config set tds.base_url http://192.168.1.100:5380
export TDS_TOKEN="<session-token-from-login>"

# 创建持久 API Token
python3 scripts/api_client.py login admin your-password tokenName=MyAutomation

# 保存到 Hermes config
hermes config set tds.token "<api-token>"
```

## 命令参考

### 会话管理

```bash
tds login [user] [pass]           # 登录并打印 token
tds logout                        # 登出当前 session
tds session                       # 获取当前 session 信息
tds profile                       # 获取用户资料
```

### 仪表盘

```bash
tds dashboard                     # 获取 metrics (JSON)
```

### 权威 Zone 管理

```bash
tds zones list                    # 列出所有 zone
tds zones create <name> <type>    # 创建 zone
  # type: Primary, Secondary, Stub, Forwarder, SecondaryForwarder, Catalog, SecondaryCatalog
tds zones delete <name>           # 删除 zone
tds zones enable <name>           # 启用 zone
tds zones disable <name>          # 禁用 zone
tds zones options get <name>      # 获取 zone 选项
tds zones perm get <name>         # 获取 zone 权限
tds zones sign <name>             # 对 zone 进行 DNSSEC 签名
tds zones unsign <name>           # 取消 DNSSEC 签名
tds zones convert <name> <type>   # 转换 zone 类型（见下文）
tds zones options set <name> key=val ...  # 修改 zone 选项
tds zones ds-info <name>          # 获取 DS 记录信息
tds zones dnssec-props <name>     # 获取 DNSSEC 属性
```

#### 创建 Zone 示例

```bash
# 创建 Primary Zone
tds zones create example.com Primary

# 创建 Conditional Forwarder Zone 并指定转发器
tds zones create internal.local Forwarder \
  initializeForwarder=true \
  forwarder=192.168.1.1 \
  protocol=Udp

# 创建 Secondary Zone
tds zones create example.com Secondary \
  primaryNameServerAddresses=1.2.3.4
```

### DNS 记录管理

⚠️ **关键参数说明**：`records add/update/delete` 的第一个位置参数是**记录的完整域名 (FQDN)**，不是 zone 名。API 的 `domain` 参数即为记录 FQDN。当记录在 zone 的根（如 `example.com` 本身）时 FQDN 等于 zone 名；当记录是子域名（如 `sub.example.com`）时 FQDN 包含 zone 后缀。如果省略 `zone=` 参数，服务器自动匹配最接近的权威 zone。

```bash
tds records get <fqdn> [--list-zone]                     # 获取记录
tds records add <fqdn> <type> key=val ...                # 添加记录
tds records update <fqdn> <type> key=val ...             # 更新记录
tds records delete <fqdn> <type> key=val ...             # 删除记录
```

#### 添加记录示例

```bash
# A 记录
tds records add example.com A ipAddress=192.168.1.10 ttl=3600

# AAAA 记录
tds records add example.com AAAA ipAddress=::1

# CNAME
tds records add example.com CNAME cname=target.example.com

# MX
tds records add example.com MX exchange=mail.example.com preference=10

# TXT
tds records add example.com TXT text="v=spf1 mx ~all"

# SRV
tds records add example.com SRV priority=10 weight=5 port=5060 target=sip.example.com

# NS (指定 glue 地址)
tds records add example.com NS nameServer=ns1.example.com glue=192.168.1.10

# PTR
tds records add example.com PTR ptrName=host.example.com

# CAA
tds records add example.com CAA flags=0 tag=issue value=letsencrypt.org

# HTTPS (SVCB)
tds records add example.com HTTPS \
  svcPriority=1 svcTargetName=. \
  svcParams="alpn|h2,h3|port|443"

# FWD (条件转发)
tds records add example.com FWD \
  forwarder=192.168.1.1 protocol=Udp

# APP 记录
tds records add example.com APP \
  appName="MyApp" classPath="MyApp.App" recordData="..."
```

#### 更新记录示例

```bash
# 更新 A 记录
tds records update example.com A ipAddress=1.2.3.4 newIpAddress=5.6.7.8

# 更新 MX
tds records update example.com MX \
  exchange=old.mail.com newExchange=new.mail.com preference=10

# 更新 TXT
tds records update example.com TXT text="old" newText="new"
```

#### 删除记录示例

```bash
tds records delete example.com A ipAddress=1.2.3.4
tds records delete example.com CNAME cname=old-target.example.com
tds records delete example.com MX exchange=mail.example.com preference=10
```

### DNS 缓存

```bash
tds cache list [domain]           # 列出缓存 zone
tds cache flush                   # 清空全部缓存
tds cache delete <domain>         # 删除特定缓存的 zone
```

### 允许列表 (Allowed Zones)

```bash
tds allowed list [domain]         # 列出允许的 zone
tds allowed add <domain>          # 添加域名到允许列表
tds allowed delete <domain>       # 从允许列表移除
tds allowed flush                 # 清空允许列表
tds allowed import <csv-domains>  # 批量导入 (逗号分隔)
```

### 阻止列表 (Blocked Zones)

```bash
tds blocked list [domain]         # 列出阻止的 zone
tds blocked add <domain>          # 添加域名到阻止列表
tds blocked delete <domain>       # 从阻止列表移除
tds blocked flush                 # 清空阻止列表
tds blocked import <csv-domains>  # 批量导入 (逗号分隔)
```

### DNS 解析查询

```bash
tds resolve <domain> [type] [options...]

# 示例
tds resolve example.com A
tds resolve example.com AAAA
tds resolve example.com MX
tds resolve google.com A --server=recursive-resolver
tds resolve example.com A --server=8.8.8.8 --protocol=Tls --dnssec=true
```

`--server` 可选值: `this-server` (本机权威/转发查询), `recursive-resolver` (递归解析), `system-dns` (系统 DNS), 或具体地址如 `8.8.8.8`

> **注意:** `resolve` 命令必须指定 `--server` 参数。使用 `--server=this-server` 查询本机 zone 和转发规则。

### 设置管理

```bash
tds settings get                  # 获取所有设置
tds settings set key=value ...    # 修改设置
```

#### 设置示例

```bash
# 开启日志查询
tds settings set logQueries=true

# 修改转发器
tds settings set forwarders=192.168.1.1,8.8.8.8

# 修改阻断类型
tds settings set blockingType=NxDomain
tds settings set blockingType=CustomAddress customBlockingAddresses=127.0.0.1

# 添加阻止列表 URL
tds settings set blockListUrls=https://big.oisd.nl/

# 启用 DNSSEC 验证
tds settings set dnssecValidation=true

# 修改监听地址
tds settings set dnsServerLocalEndPoints=0.0.0.0:53,[::]:53

# 启用 DNS-over-TLS
tds settings set enableDnsOverTls=true dnsOverTlsPort=853

# 设置 Web 服务
tds settings set webServiceEnableTls=true webServiceTlsPort=53443

# 修改缓存大小
tds settings set cacheMaximumEntries=50000

# 修改 session 超时
tds settings set sessionTimeoutSeconds=3600
```

### DNS Apps

```bash
tds apps list                     # 列出已安装的 apps
tds apps store                    # 列出 App Store 可用 apps
tds apps install <name>           # 安装 app (从 store 或 --url)
  # 从 URL 安装: tds apps install GeoIP --url=https://...
tds apps uninstall <name>         # 卸载 app
tds apps config get <name>        # 获取 app 配置
tds apps config set <name> <data> # 设置 app 配置
```

### 日志

```bash
tds logs list                     # 列出日志文件
tds logs query <app> <classPath> [options...]
  # options:
  #   --page=1 --per-page=10
  #   --start=2024-01-01 --end=2024-01-31
  #   --clientIpAddress=... --protocol=Udp
  #   --responseType=Blocked --rcode=NxDomain
  #   --qname=example.com --qtype=A

# 查询 DNS 查询日志的示例:
tds logs query "Block Page" "BlockPageWebServer.App" \
  --page=1 --per-page=50
```

### 管理 & 集群

```bash
tds admin users list              # 列出用户
tds admin users create <user> <pass> [groups=Administrators]
tds admin users delete <user>     # 删除用户
tds admin users details <user>    # 获取用户详情

tds admin groups list             # 列出组
tds admin groups create <name>    # 创建组
tds admin groups delete <name>    # 删除组

tds admin sessions                # 列出活跃会话

tds admin permissions             # 列出所有权限

tds admin cluster state           # 获取集群状态
```

## 常用工作流

### 1. Zone Type Conversion 说明

Zone type 决定了 DNS 服务器如何处理该域名的查询：

| Zone Type | 行为 | 适用场景 |
|-----------|------|----------|
| `Primary` | 完全权威，未定义记录返回 NXDOMAIN | 内部域名、完全自管的域名 |
| `Forwarder` | 未定义记录转发到上游 DNS，本地记录覆盖 | Split-horizon（内网解析 + 外网回退）|
| `Secondary` | 从 Primary 同步数据 | 多节点冗余 |
| `Stub` | 仅同步 NS 记录，查询时递归 | 委托子域名 |
| `SecondaryForwarder` | 从 Primary 同步转发配置 | 集群转发 |
| `Catalog` | 管理成员 zone 列表 | Zone 批量管理 |

```bash
# Primary → Forwarder (最常见的内网+外网回退场景)
tds zones convert example.com Forwarder

# Forwarder → Primary
tds zones convert example.com Primary

# Primary → Secondary (设置从节点)
tds zones convert example.com Secondary
```

### 2. 添加域名到阻止列表

```bash
tds blocked add doubleclick.net
tds blocked add googleadservices.com
# 批量导入
tds blocked import "tracker.example.com,ads.example.com,analytics.example.com"
# 刷新缓存使之立即生效
tds cache flush
```

### 2. 创建内部域名并添加记录

```bash
tds zones create internal.lan Primary
tds records add nas.internal.lan A ipAddress=192.168.1.10
tds records add router.internal.lan A ipAddress=192.168.1.20
tds records add files.internal.lan CNAME cname=nas.internal.lan
```

### 3. 切换 DNS 上游

```bash
# 获取当前设置
tds settings get | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response',{}).get('forwarders',[]))"

# 设置新的 forwarder
tds settings set forwarders=1.1.1.1,8.8.8.8

# 或切换到递归模式 (清空 forwarder)
tds settings set forwarders=

# 清空缓存
tds cache flush
```

### 4. 配置 DNS-over-TLS/HTTPS

```bash
tds settings set \
  enableDnsOverTls=true \
  dnsOverTlsPort=853 \
  enableDnsOverHttps=true \
  dnsOverHttpsPort=443
```

### 5. Split-Horizon DNS：内网域名 + 外网解析回退

场景：想要 `dsm.home.lan` 解析到内网 IP，但 `www.home.lan` 走外网正常解析。

方案：创建 **Forwarder** zone，添加本地记录会自动覆盖转发。

```bash
# 方式 A：直接创建 Forwarder zone
tds zones create home.lan Forwarder initializeForwarder=true \
  forwarder=1.1.1.1 protocol=Udp

# 方式 B：已有 Primary zone 时，先转换再添加转发规则
tds zones convert home.lan Forwarder
tds records add home.lan FWD forwarder=1.1.1.1 forwarderPriority=1
tds records add home.lan FWD forwarder=8.8.8.8 forwarderPriority=2

# 添加本地覆盖记录（自动优先于 FWD）
# 注意：第一个位置参数是记录 FQDN，不是 zone 名
tds records add dsm.home.lan A ipAddress=192.168.1.10
tds records add nas.home.lan AAAA ipAddress=fd00::1

# 验证
tds resolve dsm.home.lan A --server=this-server     # → 192.168.1.10 (Auth)
tds resolve www.home.lan A --server=this-server      # → 公网 IP (非Auth，转发)
```

关键原理：
- Forwarder zone 的 FWD 记录定义默认转发目标
- 同一 zone 内的 A/AAAA/CNAME 等记录比 FWD 更精确，自动优先匹配
- TTL=0 的 FWD 记录表示不缓存转发结果

### 6. 备份和还原设置

```bash
# 获取所有设置保存到文件
tds settings get > dns-settings-backup.json

# 使用 --include 恢复特定设置
# (settings set 会覆盖值，所以从备份中提取需要的 key=value 然后执行)
python3 -c "
import json
with open('dns-settings-backup.json') as f:
    d = json.load(f)['response']
# 打印成 key=value 格式
for k, v in d.items():
    if isinstance(v, bool):
        print(f'{k}={\"true\" if v else \"false\"}')
    elif isinstance(v, (int, float)):
        print(f'{k}={v}')
    elif isinstance(v, list):
        print(f'{k}={\",\".join(str(x) for x in v)}')
    elif v is not None:
        print(f'{k}={v}')
"
```

## 安全注意事项

- **登录凭证不要硬编码在脚本中**。优先使用 API Token + Hermes config 存储
- API Token 只能通过 `Authorization: Bearer` header 传递
- 建议为自动化任务创建专用用户，限制最小权限
- HTTPS 生产环境务必启用 TLS (`webServiceEnableTls=true`)
- 使用 `hermes config set tds.token <token>` 存储 token，避免明文环境变量
- token 会自动从 Hermes config 读取，不需要额外 export

## 常见陷阱

### `records add/update/delete` 的 `domain` 参数覆盖问题

`api_client.py` 中 `records` 命令的第一个位置参数映射到 API 的 `domain` 参数（**记录 FQDN**）。后续的 `key=value` 参数中如果出现了 `domain=`，会**覆盖**第一个位置参数，导致服务器找不到正确的 zone。

**错误示例**：
```bash
# 错误 — 'domain=app01' 覆盖了 'domain=local'，服务器查找 zone 'app01' 失败
tds records add local A domain=app01 ipAddress=192.168.69.1

# 错误 — 'domain=dsm' 覆盖了 'domain=home.lan'
tds records add home.lan A domain=dsm ipAddress=192.168.1.10
```

**正确写法**（用 FQDN 作为第一个参数）：
```bash
# 子域名 — FQDN 作为第一个参数
tds records add app01.local A ipAddress=192.168.69.1

# zone 根 — FQDN 等于 zone 名
tds records add home.lan FWD forwarder=1.1.1.1

# 显式指定 zone（避免自动匹配歧义）
tds records add sub.other.lan A ipAddress=10.0.0.1 zone=other.lan
```

- 详情见 `references/api-notes.md`

## 故障排查

### 常见错误

| 响应 status | 原因 |
|-------------|------|
| `invalid-token` | Token 过期或无效，重新 login |
| `2fa-required` | 需要提供 TOTP 验证码 |
| `error` | 检查 `errorMessage` 字段详细说明 |

### 连接问题

```bash
# 测试基本连接
curl -s http://localhost:5380/api/user/session/get \
  -H "Authorization: Bearer $TDS_TOKEN"

# 检查服务器是否运行
curl -s -o /dev/null -w "%{http_code}" http://localhost:5380/

# 查看详细错误
python3 scripts/api_client.py session 2>&1
```

## 参考

- 完整 API 文档: https://github.com/TechnitiumSoftware/DnsServer/blob/master/APIDOCS.md
- 项目主页: https://technitium.com/dns/
- 变更日志: https://github.com/TechnitiumSoftware/DnsServer/blob/master/CHANGELOG.md
