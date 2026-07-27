# {{DATABASE}} database_profile

版本日期：{{DATE}}

## 使用说明

本文件用于新数据库进入变量定义工位前的 profile。每个数据库先填一份 profile，再开始第一个主题。  
profile 的目的不是替代 官方问卷详情，而是固定“哪些信息必须先搞清楚”，避免把 CHARLS 变量名、波次结构或下载方式直接套到其它数据库。

建议保存位置：

```text
<DBCODEBOOK_HOME>\演示\定义\_数据库profile\{{DATABASE}}_profile.md
```

## 1. 数据库基本信息

| 项目 | 内容 |
| --- | --- |
| 数据库名 | `{{DATABASE}}` |
| 数据库中文名 | {{DATABASE_CN}} |
| bookapp 入口 | `{{BOOKAPP_URL}}` |
| 数据类型 | 纵向 / 横断面 / 重复横断面 / 其它 |
| 年份或周期 | {{YEARS_OR_CYCLES}} |
| 主 ID | `{{ID_VAR}}` |
| 人级 ID / 家庭 ID / 访谈 ID | {{ID_STRUCTURE}} |
| 权重变量 | {{WEIGHT_VARS_OR_NA}} |
| 当前 profile 状态 | 草稿 / 已验证 / 需返修 |

## 2. 数据结构与合并规则

| 检查项 | 结论 | 证据或备注 |
| --- | --- | --- |
| 一行代表什么 | 个人-波次 / 个人-周期 / 其它 |  |
| `year` / wave / cycle 来源 |  |  |
| 是否存在跨文件合并 | 是 / 否 |  |
| 是否存在不同样本子集 | 是 / 否 |  |
| 是否存在访谈状态或响应状态变量 | 是 / 否 |  |
| 是否存在重复 ID | 是 / 否 / 未查 |  |
| 缺失编码习惯 | 例如 `.d`、`.r`、-8、-9、NA |  |
| 标签语言 | 英文 / 中文 / 混合 |  |

## 3. bookapp 使用规则

| 项目 | 内容 |
| --- | --- |
| 常用入口 | `http://localhost:8000/home/{{DATABASE_LOWER}}/` |
| 目录检索方式 | 目录检索 / 关键词搜索 / 批量输入 / 其它 |
| 官方问卷详情必须核验 | 题干、年份/周期、取值标签、跳题/路由、样本限制、变量所在文件 |
| 批量输入格式 | `varname (file)=varname` 或数据库实际格式 |
| 官方问卷详情 fallback | 文本定位失稳时可截图定位 + 坐标点击；过程卡必须记录截图路径、页面路径、变量名、单元格/字段、核验结论 |
| 不允许的捷径 | 只凭变量名、只凭旧代码、只凭 Easy label、只凭搜索结果标题 |

## 4. 下载与 raw 恢复规则

### localhost 场景

默认流程：

```powershell
& <DBCODEBOOK_BOOKAPP_ROOT>\venv\Scripts\python.exe <SKILL_ROOT>\scripts\recover_bookapp_export.py `
  --db {{DATABASE_LOWER}} `
  --latest `
  --out "<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}" `
  --expect-vars {{RAW_VARS_CSV}}
```

要求：

- [ ] 优先使用 `--latest`，不常规进入个人中心人工查 transaction id。
- [ ] `--expect-vars` 必须与页面预览变量顺序一致。
- [ ] `recover_bookapp_export_QA.txt` 必须包含 `transaction_selection` 和 `matching_transaction_ids`。
- [ ] 恢复 QA 移入过程目录，不留在正式成果目录。
- [ ] `--latest` 失败时才回退 `--transaction`，并记录失败原因。

### 正式域名场景

| 项目 | 规则 |
| --- | --- |
| 域名 | `https://dbcodebook.cn` / 其它 |
| 下载落盘位置 | {{DOWNLOAD_LOCATION}} |
| 是否能用后端恢复工具 | 是 / 否 / 未验证 |
| 回退方式 | 浏览器下载文件 / 个人中心找回 / 手工移动到正式目录 / 其它 |
| 必须记录 | 下载时间、下载记录、变量清单、文件 SHA 或行列数 |

## 5. 命名与变量口径规则

| 项目 | 当前数据库规则 |
| --- | --- |
| 默认重要变量前缀 | `A_` / 其它 |
| 专题变量前缀 | 例如 `PA_` |
| YES/NO 变量 | 用 `1/0` |
| 多分类变量 | 保留解码标签，不直接用纯数字 |
| 连续变量 | 记录单位、合理范围、异常值处理 |
| 总分或总量变量 | 明确分项为 0 / NA 的规则；任一分项 NA 时总量是否 NA |
| 分类区间换算 | 说明取下限 / 中点 / 上限，区间值用加粗，不用反引号 |
| 中间过程变量 | 不进入 `analysis_db`，除非用户明确要求 |

## 6. 数据库特有坑清单

| 坑 | 影响主题 | 具体表现 | 处理规则 | 是否已沉淀 |
| --- | --- | --- | --- | --- |
| 同名变量跨波次语义漂移 |  |  |  | [ ] |
| 预载变量 / 上轮变量 |  |  |  | [ ] |
| 路由变量容易误入主定义 |  |  |  | [ ] |
| 某波次缺少严格历史来源 |  |  |  | [ ] |
| 标签与原值混合 |  |  |  | [ ] |
| 特殊缺失编码 |  |  |  | [ ] |
| 样本子集限制 |  |  |  | [ ] |
| 周期结构不是 wave/year |  |  |  | [ ] |

## 7. 主题编号与已完成清单

同一主题跨数据库沿用同一个编号；新主题先查 `主题索引.md`，没有再分配新编号。

| 编号 | 主题 | 当前数据库状态 | 正式目录 | 验收状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 001 | 吸烟状态 | 未开始 / 进行中 / 已完成 | `<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\001_吸烟状态` | 未验收 |  |
| 002 | 饮酒状态 | 未开始 / 进行中 / 已完成 | `<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\002_饮酒状态` | 未验收 |  |
| 003 | 运动时间 | 未开始 / 进行中 / 已完成 | `<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\003_运动时间` | 未验收 |  |
| 004 | 睡眠 | 未开始 / 进行中 / 已完成 | `<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\004_睡眠` | 未验收 |  |

## 8. R 与输出规范

固定工具：

- `<SKILL_ROOT>\scripts\run_r_definition.ps1`
- `<SKILL_ROOT>\scripts\check_definition_output.py`
- `<SKILL_ROOT>\assets\qa-safe-summary.R`

R 规则：

- [ ] 正式脚本按通用定义规范写包检查块；缺少 `devtools`、`openxlsx`、`dplyr` 时可自动 `install.packages()`。
- [ ] 如果使用 `dbCodeBookr`，必须在 `library("dbCodeBookr")` 前写 `install_github("ZhidoHuang/dbCodeBookr") # 提示更新包, 可选3跳过，首次使用时需要安装`。
- [ ] 正式 R 脚本为 UTF-8 without BOM。
- [ ] mapping 追溯 raw 变量，不映射到中间过程变量。
- [ ] 正式 R 运行使用 `run_r_definition.ps1`，最终 log 必须包含 `Rscript exit code: 0`。

正式目录标准交付物：

- `bookapp_download.zip`
- `raw_data.csv`
- `raw_codebook.csv`
- `define_{{DATABASE_LOWER}}_{{TOPIC_EN}}.R`
- `db_{{PREFIX}}{{TOPIC_SHORT}}.xlsx`
- `codebook_{{PREFIX}}{{TOPIC_SHORT}}.xlsx`
- `analysis_db_{{PREFIX}}{{TOPIC_SHORT}}.xlsx`
- `analysis_codebook_{{PREFIX}}{{TOPIC_SHORT}}.xlsx`
- QA 文本
- definition HTML
- detail HTML
- 笔记 md
- 一个最终成功 log

禁止正式目录残留：

- `*_defined.csv`
- `.rds`
- 单独 consistency xlsx
- 多余 md
- 多个正式 log
- 工具 QA
- 自检 json

## 9. 验收规则

执行线程回传前必须完成：

- [ ] bookapp 证据摘要
- [ ] raw 变量清单
- [ ] 下载恢复 QA
- [ ] R 运行 log 收口
- [ ] 自检 json `ok: true`
- [ ] 成果审核包
- [ ] 执行流程复盘包

以下事项由执行任务机器闭环核验，不再交给独立验收重复检查：

- [ ] 正式目录文件清单
- [ ] raw/header/codebook 行列数
- [ ] analysis_db 维度与列名
- [ ] analysis_codebook 变量列表
- [ ] 禁止变量和禁止产物
- [ ] QA/HTML/笔记口径一致性
- [ ] log 尾部退出码
- [ ] 过程卡是否记录已知坑回顾和新增坑

大脑入账条件：

- [ ] 机器闸门通过；如存在机器证据冲突、未决研究问题、公共核心机制边界不足或用户明确要求，限定范围独立验收已 PASS
- [ ] 无正式成果阻断问题
- [ ] 若有流程观察项，已裁决为工具化 / 流程化 / 模板化 / profile 化 / 不沉淀

## 10. 本数据库第一轮试跑计划

建议新数据库第一轮只做一个主题，优先 `001_吸烟状态`。

| 步骤 | 内容 | 状态 |
| --- | --- | --- |
| 1 | 填完本 profile 草稿 | [ ] |
| 2 | 大脑派发 `001_吸烟状态` | [ ] |
| 3 | 执行线程跑完整流程 | [ ] |
| 4 | 机器闸门；仅异常或明确要求时启动限定范围独立验收 | [ ] |
| 5 | 根据新增坑更新 profile / 工具 / 流程 | [ ] |
| 6 | 再决定是否继续 `002_饮酒状态` | [ ] |

