---
name: ai-skill-creator
description: |
  AI公司 Skill 创作工作流（CTO MLOps + CISO securitystandard版）。当需要从头create新 Skill（包括初始化目录结构、编写 SKILL.md、引用文件、脚本资源、securityreview、quality gate）时使用。trigger关键词：createSkill、新建 Skill、开发 Skill、create skill、新建Skill包。integrate CTO MLOps 生命cycle6phase + CISO securityreviewstandard（STRIDE + CVSS + security门禁），最终输出符合 ClawHub/VirusTotal reviewstandard的可publish .skill 包。
metadata:
  version: 1.1.0
  openclaw:
---

# <Skill 名称>

## Overview（<10行）

## 核心Function（模块化，每个<50行）

## security考虑（如有）

## 常见错误
```

#### Frontmatter 必需字段

| 字段 | 要求 | 示例 |
|------|------|------|
| `name` | 英文小写+连字符 | `pdf-processor` |
| `version` | semver X.Y.Z | `1.0.0` |
| `description` | >50字，描述trigger时机 | 见上方模板 |
| `metadata.openclaw.emoji` | 1个 emoji | `"🔒"` |
| `metadata.openclaw.os` | 支持的 OS | `["linux","win32"]` |

#### 目录结构standard
- ✅ `SKILL.md`（必需）
- ✅ `scripts/`（可选，脚本需测试）
- ✅ `references/`（可选，详细文档放此处）
- ✅ `assets/`（可选，静态资源）
- ❌ `README.md`（prohibit）
- ❌ `CHANGELOG.md`（prohibit）
- ❌ `INSTALLATION_GUIDE.md`（prohibit）

**CISO security架构review**：

| 威胁类型（STRIDE）| defend措施 |
|-----------------|---------|
| **S**poofing | Skill 名称不得伪造系统命令 |
| **T**ampering | 所有文件path需verify，不接受动态path拼接用户输入 |
| **I**nfo Disclosure | prohibit在 Skill 中硬编码密钥/令牌 |
| **D**enial of Service | prohibit无限循环/递归的文件操作 |
| **E**levation | permission不得超出design范围 |

---

### Phase 3 — 实现（Implementation）

**输出**：完整的 `SKILL.md`、`scripts/`、`references/`、`assets/`

#### SKILL.md 编写standard

**描述字段（description）必须包含**：
1. **trigger关键词**（用户说什么会激活此 Skill）
2. **execute动作**（Skill 做什么）
3. **文件格式**（输入/输出文件类型）
4. **security边界**（如果涉及敏感操作）

**Body 编写principle**：
- 使用命令式/不定式语气（"Use X to do Y"，"Do not use Z"）
- 避免冗余解释（Claude 已经很聪明）
- 代码示例优先于文字Description
- 引用文件链接到 `references/`（渐进式披露）

#### 脚本编写standard

**必须遵守**：
```markdown
## 脚本security红线（🚨 违反即reject）

🚫 prohibit：
• curl/wget 到未知 URL
• 将data发送到外部服务器
• 请求凭证/令牌/API密钥（环境变量接收除外）
• 读取 ~/.ssh ~/.aws ~/.config 等敏感目录
• 访问 MEMORY.md USER.md SOUL.md IDENTITY.md
• 使用 base64 decode 未知内容
• 使用 eval()/exec() handle外部输入
• 修改 workspace 外的系统文件
• 安装包但不列出所需依赖
• 网络调用到裸 IP（非域名）
• 混淆代码（压缩/编码/混淆）
• 请求enhancepermission/sudo
• 访问浏览器 cookie/session
```

**脚本必须包含**：
1. 用途Description（注释）
2. 输入参数Description
3. 输出Description
4. 错误handle
5. security检查（如适用）

#### 资源文件standard

| 资源类型 | 存放位置 | standard |
|---------|---------|------|
| 参考文档 | `references/` | >100行需加目录导航 |
| 脚本 | `scripts/` | 需可execute测试 |
| 静态资源 | `assets/` | 不加载到上下文 |

---

### Phase 4 — securityreview（Security Review）

> ⚠️ **强制门禁**：CISO review必须通过，否则prohibitpublish

**reviewprocess**：

#### Step 1：代码review（MANDATORY）

逐文件review，查找以下 **RED FLAGS**：

```
🚨 REJECT IMMEDIATELY IF YOU SEE:
─────────────────────────────────────────
• curl/wget → 未知 URL
• data发送 → 外部服务器
• 凭证请求 → 密钥/令牌
• 读取 ~/.ssh ~/.aws ~/.config
• 访问 MEMORY/USER/SOUL/IDENTITY.md
• base64 decode → 未知内容
• eval() / exec() → 外部输入
• 修改 workspace 外文件
• 安装包 → 未列依赖
• 网络调用 → 裸 IP
• 混淆代码
• 请求 sudo/enhancepermission
• 访问浏览器 cookie
• 接触凭证文件
─────────────────────────────────────────
```

#### Step 2：permissionassess

| permission类型 | 检查项 | 决策 |
|---------|--------|------|
| 文件读取 | 列出所有读取path | verify合理性 |
| 文件写入 | 列出所有写入path | 限定 workspace |
| 命令execute | 列出所有命令 | verify必要性 |
| 网络访问 | 列出所有域名/IP | verify可信度 |

#### Step 3：依赖扫描

```bash
# 检查脚本中声明的依赖
# Node.js: npm list <package>
# Python: pip freeze | grep <package>
# verify无已知 CVE（CVSS ≥ 7.0）
```

#### Step 4：漏洞评分（CVSS）

| CVSS | 严重性 | 决策 |
|------|--------|------|
| 9.0-10.0 | Critical | 🚫 rejectpublish |
| 7.0-8.9 | High | 🚫 rejectpublish，修复后重审 |
| 4.0-6.9 | Medium | ⚠️ notify用户，可修复后publish |
| 0.1-3.9 | Low | ✅ 通过 |

#### Step 5：STRIDE 威胁建模

| 威胁 | assess问题 | defendplan |
|------|---------|---------|
| S | Skill 名称是否可被劫持？ | prohibit与系统命令同名 |
| T | path参数是否可注入？ | verify输入，reject `../` |
| R | 操作是否可否认？ | record操作日志（引用文件） |
| I | 敏感data是否泄露？ | PII 过滤，密钥不放代码 |
| D | 是否有 DoS risk？ | 资源restrict，超时中断 |
| E | permission是否超出最小permission？ | review工具permission列表 |

**securityreviewreport模板**：

```
════════════════════════════════════════════════════
SKILL SECURITY REVIEW REPORT
════════════════════════════════════════════════════
Skill: <name>
Version: <version>
Reviewer: CISO-001
Date: <ISO date>
────────────────────────────────────────────────────
🔴 RED FLAGS: [None / List with CVSS scores]

🟡 PERMISSIONS REVIEW:
• Files Read:  [list]
• Files Write: [list]
• Commands:    [list]
• Network:     [list]

🟢 STRIDE MODELING:
• S (Spoofing):  [Pass/Fail] — <reason>
• T (Tampering): [Pass/Fail] — <reason>
• R (Repudiation):[Pass/Fail] — <reason>
• I (Info Disclosure): [Pass/Fail] — <reason>
• D (Denial of Service):[Pass/Fail] — <reason>
• E (Elevation):  [Pass/Fail] — <reason>

📊 CVSS SCORE: <X.Y> (<severity>)
────────────────────────────────────────────────────
VERDICT: [✅ APPROVED / 🚫 REJECTED / ⚠️ CONDITIONAL]

ACTION ITEMS: [list if any]
════════════════════════════════════════════════════
```

---

### Phase 5 — quality gate（Quality Gate）

**CTO 强制quality gate（全部通过方可publish）**：

| 质量门 | 检查项 | 工具/方法 | 通过standard |
|--------|--------|---------|---------|
| **G0** 文件结构 | 目录结构符合standard | 人工检查 | 4个目录齐全 |
| **G1** Frontmatter | YAML 格式正确，必需字段存在 | 解析 YAML | name/description/version/emoji 齐全 |
| **G2** 描述质量 | description > 50字，含trigger关键词 | 人工review | 包含trigger时机+execute动作 |
| **G3** security扫描 | 无 RED FLAGS，无高危漏洞 | Phase 4 review | CVSS < 7.0 |
| **G4** 文档完整性 | 核心process有Description，引用文件有链接 | 人工review | 无悬空引用 |
| **G5** 脚本测试 | scripts/ 下脚本可execute | 实际运行测试 | 零报错 |

**Quality Gate Checklist**（save至 `references/quality-gate.md`）：

```markdown
## Quality Gate Checklist

- [ ] G0: 目录结构正确（SKILL.md + scripts/ + references/ + assets/）
- [ ] G1: Frontmatter 完整（name, version, description, emoji）
- [ ] G2: description > 50字，含trigger关键词
- [ ] G3: CISO securityreview通过（CVSS < 7.0，STRIDE 无 FAIL）
- [ ] G4: references/ 中文档有链接Description，无悬空引用
- [ ] G5: 所有 scripts/ 脚本已测试，零报错
- [ ] G6: SKILL.md < 500行（渐进式披露正确）
- [ ] G7: 无prohibit文件（README.md/CHANGELOG.md 等）
```

---

### Phase 6 — 打包与publish（Package & Publish）

**使用 package_skill.py 打包**：

```powershell
# Windows
python.exe <openclaw_path>\skills\skill-creator\scripts\package_skill.py <path/to/skill-folder> <output-dir>

# Linux/macOS
python3 <openclaw_path>/skills/skill-creator/scripts/package_skill.py <path/to/skill-folder> <output-dir>
```

**打包脚本自动execute**：
1. ✅ verify YAML frontmatter 格式
2. ✅ 检查 Skill 命名standard
3. ✅ verify目录结构
4. ✅ 检查 description 完整性
5. ✅ confirm文件组织
6. ✅ 打包为 `.skill` 文件

**publish到 ClawHub**：

```bash
# 登录（如需publish到公共仓库）
clawhub login

# publish
clawhub publish ./<skill-name> \
  --slug <skill-name> \
  --name "<Skill 显示名称>" \
  --version X.Y.Z \
  --changelog "<变更Description>"
```

**publish前最终检查**：

```markdown
## publish前 Checklist

- [ ] CISO securityreviewreport已生成（Phase 4）
- [ ] Quality Gate 全部通过（Phase 5）
- [ ] .skill 包文件已生成
- [ ] 版本号符合 semver（X.Y.Z）
- [ ] Changelog 已写入（如果已有历史版本）
- [ ] ClawHub slug 已confirm唯1性
```

---

## 快速参考

### trigger命令

```
"create Skill" / "新建Skill" / "开发 Skill" / "create1个Skill包"
```

### 自然语言指令映射

| 用户请求 | execute动作 |
|---------|---------|
| "create1个读取 PDF 的 Skill" | 初始化 → 需求analyze → 架构design → 实现 → securityreview → 打包 |
| "帮我写1个handle Excel 的Skill" | 同上，参考 xlsx skill design模式 |
| "需要1个新 Skill 来做 XX" | 需求analyze → confirmtrigger时机和permission |

### 常见错误

1. **跳过securityreview**：Phase 4 是强制门禁，不得跳过
2. **手动create目录**：必须使用 init_skill.py
3. **SKILL.md 过长**：超过 500 行 → 拆分到 references/
4. **description 过短**：< 50 字 → trigger时机不明确，Skill 无法激活
5. **引入prohibit文件**：README.md/CHANGELOG.md → 删除
6. **硬编码密钥**：🚫 reject，必须用环境变量

---

## 参考文件

- `references/design.md` — 需求analyze模板和架构design指南
- `references/security-review.md` — 详细 CISO securityreview清单
- `references/quality-gate.md` — quality gate检查表
- `references/publish-guide.md` — ClawHub publish指南

---

## 版本历史（Changelog）

| 版本 | 日期 | Changes | 审核人 |
|------|------|---------|--------|
| **1.1.0** | 2026-04-13 | 新增 Agent 调用接口层（Inter-Agent Interface）：6个 Task 类型（create/design-review/security-review/quality-gate/package/publish）；CISO securityConstraint和security红线；与 ai-skill-maintainer / ai-skill-optimizer 接口关系Definition；CLO compliance登记节点；Day 3 预算概算 | CTO-001 / CISO-001 |
| **1.0.0** | 2026-04-11 | Initial version：CTO MLOops 6phase创作process + CISO STRIDE securityreviewstandard + G0-G7 quality gate | CTO-001 / CISO-001 |

## rollbackstrategy（Rollback）

> 如任何phase失败，execute以下操作recover：

```bash
# recover到上1个 Git tag
git checkout tags/v<上1版本> -- .

# 或使用快照包（如果有）
clawhub restore ./dist/<skill-name>-v<X.Y.Z>.skill

# verifyrollback成功
git log --oneline -3
```

**rollbacktrigger条件**：
- Phase 3（G2 securityreview）失败 → rollback到 Phase 2
- Phase 4（G3 quality gate）失败 → rollback到 Phase 3
- Phase 6（publish）失败 → rollback到 Phase 5

**rollback后操作**：
1. recordrollback原因到 `references/creation-log.md`
2. notify CTO-001 和 CISO-001
3. analyze失败原因后重新进入创作process
