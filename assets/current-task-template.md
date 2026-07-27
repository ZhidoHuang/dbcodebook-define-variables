# {{DATABASE}} {{TOPIC_ID}}_{{TOPIC_NAME}} current_task

正式源说明：启用本 Skill 后，本模板的唯一正式位置是 `<SKILL_ROOT>\assets\current-task-template.md`。工作区中的同名旧模板不得作为规则依据。

## 任务边界

- 线程身份：固定定义执行线程，不是大脑线程。
- 项目根目录：`<DBCODEBOOK_HOME>\演示`
- 正式目录：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}`
- 过程目录：`<DBCODEBOOK_HOME>\演示\定义\_执行线程\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}`
- 旧目录仅作历史参考，不覆盖、不修改：`{{OLD_DIR}}`
- 本轮只做：`{{TOPIC_ID}}_{{TOPIC_NAME}}`
- 下一主题：不启动，除非大脑明确派发。

## 开工前同步

- [ ] 读取 `<SKILL_ROOT>\references\directory-structure.md`
- [ ] 读取 `<DBCODEBOOK_HOME>\演示\定义\_索引\主题索引.md`
- [ ] 读取 `<DBCODEBOOK_HOME>\演示\定义\_索引\定义验收台账.md`
- [ ] 读取 `<SKILL_ROOT>\references\charls-workflow.md`
- [ ] 读取 `<SKILL_ROOT>\references\charls-profile.md`；只把其中主题经验当作避坑参考，不机械套用到本主题
- [ ] 读取 `<SKILL_ROOT>\references\user-material-rules.md`
- [ ] 读取 `<SKILL_ROOT>\references\project-governance.md`
- [ ] 读取旧结构最终成果和过程卡，确认最新口径，防止旧草案回潮。

## 上轮坑回顾

开工前必须回顾最近同类任务的踩坑复盘包，并写明本轮如何避免复发。

| 已知坑 | 来源任务 | 本轮预防动作 | 是否已落实 |
| --- | --- | --- | --- |
| 下载记录人工查找 / transaction id | `{{PREV_TASK_1}}` | 优先使用 `recover_bookapp_export.py --latest` | [ ] |
| 旧标签状态污染 / 清空确认框 | `{{PREV_TASK_1}}` | 新开干净 bookapp 标签，不优先清空旧标签 | [ ] |
| 正式 log 无退出码 | `{{PREV_TASK_2}}` | 使用 `run_r_definition.ps1` | [ ] |
| R 脚本 UTF-8 BOM | `{{PREV_TASK_2}}` | 正式运行前由 `run_r_definition.ps1` 阻断；脚本保存为 UTF-8 without BOM | [ ] |
| 回传前机械问题未自检 | `{{PREV_TASK_2}}` | 使用 `check_definition_output.py` | [ ] |
| QA / HTML / 笔记口径不一致 | `{{PREV_TASK_2}}` | Criteria 文本同步生成或逐项关键词自检 | [ ] |

如果本轮再次出现上表中的坑，必须标记为“复发”，并在过程卡中说明为什么既有规则没有挡住。

## 本轮变量口径

- 变量前缀：`{{PREFIX}}`
- 预计最终分析变量：
  - `{{VAR_1}}`
  - `{{VAR_2}}`
  - `{{VAR_3}}`
- 禁止变量：
  - `{{FORBIDDEN_VAR_1}}`
- 禁止成果：
  - `*_defined.csv`
  - `*.rds`
  - 多个零散 md
  - 单独 consistency disclosure xlsx
  - 多个正式运行 log

## bookapp 页面流程

- 页面：`http://localhost:8000/home/{{DATABASE_LOWER}}/`
- 目录检索关键词：`{{SEARCH_KEYWORD}}`
- 目录路径：**{{BOOKAPP_PATH}}**
- 官方问卷详情核查：
  - [ ] 原始变量语义
  - [ ] 波次差异
  - [ ] 取值与路由
  - [ ] 排除变量理由
- 官方问卷详情 fallback 证据，只有文本 locator 失稳或页面控件异常时填写：
  - 截图路径：
  - 页面路径：
  - 变量名：
  - 单元格/字段：
  - 核验结论：
- 页面选择 raw 变量：
  - `{{RAW_VAR_1}}`
  - `{{RAW_VAR_2}}`
- 预览确认：
  - [ ] 已选择变量数正确
  - [ ] header 正确
  - [ ] 记录数合理
  - [ ] 禁止变量未出现
- 下载记录：
  - 时间：
  - `--latest` 匹配结果或 transaction id：

## 针对性文献调研

本节在初步候选形成后、变量选择与下载前完成。详细规则只以 `CHARLS变量定义标准流程.md` 的“针对性文献调研与候选闸门”为准。

- 实际检索日期：
- 检索平台/来源：
- 实际检索式：
- 是否属于必须实质调研的量表、认知测验、总分、指数、复合变量或多口径主题：

| 来源 | 证据等级 | 周期/样本 | 研究概念 | 项目/raw | 计分与范围 | 缺失/完整性 | 与本轮候选的关系 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 官方原始 / 技术文档 / 原始方法或制度 / 高质量直接研究 / 一般应用 |  |  |  |  |  |  |

- 推荐方案及依据：
- 仍需裁决的问题：
- 候选闸门状态：`PENDING / USER_DECISION_REQUIRED / APPROVED`
- [ ] 候选闸门未通过前未下载 raw、未编写正式 R、未生成正式成果

## localhost raw 恢复

恢复命令：

```powershell
& <DBCODEBOOK_BOOKAPP_ROOT>\venv\Scripts\python.exe <SKILL_ROOT>\scripts\recover_bookapp_export.py `
  --db {{DATABASE_LOWER}} `
  --latest `
  --out "<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}" `
  --expect-vars {{RAW_VARS_CSV}}
```

回退命令，仅当 `--latest` 无法匹配本次下载记录时使用：

```powershell
& <DBCODEBOOK_BOOKAPP_ROOT>\venv\Scripts\python.exe <SKILL_ROOT>\scripts\recover_bookapp_export.py `
  --db {{DATABASE_LOWER}} `
  --transaction <transaction_id> `
  --out "<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}" `
  --expect-vars {{RAW_VARS_CSV}}
```

恢复 QA：

- [ ] `result: PASS`
- [ ] 优先使用 `--latest`；若回退到 `--transaction`，已记录回退原因
- [ ] `raw_data.csv` header 正确
- [ ] `raw_codebook.csv` 变量正确
- [ ] `recover_bookapp_export_QA.txt` 移入过程目录

## R 正式运行

使用固定 R runner：

```powershell
& <SKILL_ROOT>\scripts\run_r_definition.ps1 `
  -WorkDir "<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}" `
  -Script "{{R_SCRIPT}}" `
  -LogPrefix "{{LOG_PREFIX}}" `
  -ArchiveDir "<DBCODEBOOK_HOME>\演示\定义\_执行线程\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\archived_logs"
```

运行要求：

- [ ] 正式目录直接运行同一份正式脚本
- [ ] `library()` 前包含 `for (pkg in c("devtools", "openxlsx", "dplyr")) { ... install.packages(pkg) ... }`
- [ ] `library("dbCodeBookr")` 前一行包含 `install_github("ZhidoHuang/dbCodeBookr") # 提示更新包, 可选3跳过，首次使用时需要安装`
- [ ] 读取 raw 使用 `dt <- read.csv("raw_data.csv")`；读取 codebook 使用 `name_z <- read.csv("raw_codebook.csv")`
- [ ] 已有 `data[data == ""] <- NA`，未再默认写 `data[data == "null"] <- NA`
- [ ] 笔记 R 代码块截取到 `# 输出` 之前，包含读取 raw、定义变量和正式输出主线
- [ ] 公开 R 使用 `# ----------- 标题 -----------` 形成可提取代码大纲；主要分段按实际顺序覆盖环境与包、读取数据、主要定义处理、`变量字典` 和正式输出，且没有空标题
- [ ] 每个正式 analysis 变量均通过 `map <- add_mapping(map, "变量名", raw_sources)` 登记全部 raw 来源，map 驱动 codebook 的 `original_vars` / `processed_vars` / `count`，未直接手填绕过
- [ ] `# 输出` 之后放 QA、HTML、笔记拼装、可视化 helper 和 `tidyr` 等只服务材料生成的依赖
- [ ] 笔记公开代码块未混入 QA、HTML、detail、笔记拼装或可视化 helper
- [ ] 正式 R 脚本为 UTF-8 without BOM；若 runner 报 BOM，先改编码再运行
- [ ] 正式分类编码默认使用英文/ASCII；中文分类提示只写入注释/说明，除非用户明确要求中文作为正式取值
- [ ] 字符重编码按 `recode.chr(data$具体变量)` 生成代码风格保留具体变量注释和固化后的 `case_when()`；代码应逐项枚举真实原值并用 `==` 精确匹配，不得写泛化 `# recode.chr(x)`，不得用 `grepl()` / 正则伪装成 recode 生成代码
- [ ] 数值重编码按 `recode.num(data$具体变量)` 生成代码风格保留具体变量注释和固化后的重编码代码
- [ ] 多个候选变量按优先级合并时优先使用 `yyds_coalesce()`
- [ ] 涉及数值、时间、频次、金额、时长、计数、总分或连续换算的 raw 变量，已扫描 `997` / `998` / `999`；已确认它们是特殊编码还是合法真实值，并在 QA 中记录出现次数和处理方式
- [ ] 长代码块有块级注释，解释为什么这样定义、解决什么数据问题、对最终变量有什么影响
- [ ] 用户版笔记不写常规缺失处理、内部 QA 话术、`transaction` / `raw_codebook` / `explicit` 等技术黑话
- [ ] 摘要导读按新版结构生成：前半 1-2 段说明数据检索和概念辨析、本轮定义边界；后半使用一张概念级摘要表
- [ ] 概念级摘要表表头为 `定义变量 | 含义 | 原始变量数 | 覆盖周期 | 对象`；允许这一张表，但不得出现逐年 raw/定义逻辑明细表
- [ ] 摘要周期术语由 analysis 周期列决定：CHARLS `year` 直接显示年份数字并使用“覆盖年份”，ELSA `wave` 使用 `Wave` / “覆盖波次”
- [ ] 覆盖全部目标周期时五列表写“全周期”；仅部分覆盖时才列具体年份或 Wave
- [ ] 摘要导读结构表的 `覆盖周期` / `对象` 已逐行显式填写；R 源中不存在 `summary_row(..., period = "全周期", object = "全样本")` 或同类默认参数
- [ ] `对象` 字段按定义变量在覆盖周期内的有效覆盖率判断：各覆盖周期均 `>= 85%` 才写 `全样本`，低于 `85%` 用整十百分比概括；过程卡/自检记录覆盖率依据
- [ ] `对象` 字段所有周期均 `>= 85%` 时写“全样本”；混合覆盖时高覆盖组优先，低覆盖按整十百分比分组，各组以 `；<br>` 分行，未写“其余覆盖年份/波次”
- [ ] 摘要导读不列逐年 raw 变量明细，不写每年使用哪个变量，不写 `年份 | 变量 | 定义逻辑` 或类似表头
- [ ] 摘要导读不写具体样本条数
- [ ] 摘要导读不出现提示式或内部话术：`见 QA`、`见下方`、`具体规则保留在定义说明中`、`使用时先判断`、`transaction`、`recover`、`自检`、`验收`
- [ ] 摘要五列表前为 1-2 个自然段，依次完成相邻概念辨析和纳入/排除边界说明；不写“本次/本轮”等制作话术，不复述 Criteria 逐项计分细节
- [ ] 笔记摘要、definition/detail HTML 正文、Criteria 和公开 R 代码注释不交代制作来源、工具名称、旧版本史或实现决策
- [ ] 用户材料每一句均已按三问判断：是否帮助识别研究对象/适用范围/变量含义，是否帮助复现或审视数据逻辑，是否影响分析选择、可比性判断或结果解释；三者皆否的内容已移到过程卡、证据链或 QA
- [ ] 用户材料已按独立生成源分区核验：摘要导读、Criteria、detail 组分/标签文案、笔记公开 R 代码段均单独检查；如已存在宣传 SVG，也单独检查
- [ ] definition `Criteria` 从 R 生成源头统一处理：小标题单独一行并加粗；内容使用轻量缩进块；多条定义逻辑/注意点用 `① ② ③`；分类分项用 `-`
- [ ] Criteria 信息层级正确：`定义` 只写变量是什么；`定义逻辑` 忠实呈现正式代码的判定口径，但未逐句照译代码，已按“判断信息 → 赋值或计算 → 缺失处理”的读者顺序组织；`分类` 只解释最终编码；`注意点` 只写不参与代码判定但影响追溯、理解、比较或使用的数据事实
- [ ] Criteria 的语言调整未新增事实；数字、阈值、权重、区间边界、来源变量、周期对应、优先级、反向计分和完整性条件均可追溯到正式代码、原始标签或明确用户裁决，未根据上下文自行补全
- [ ] 定义逻辑中的程序语法已在不改变结果的前提下改写为实际判定结果；未向读者暴露不必要的函数名、中间对象、取余或嵌套分支
- [ ] Criteria 已从正式代码、raw 标签和明确业务裁决重新组织，未把旧 Criteria 文案当作权威改写底稿
- [ ] 未把 `TRUE ~ NA`、未匹配类别或防御性兜底机械写成“不属于这些选项时保留缺失”；具体特殊值已按 raw 标签直说，纯防御分支已省略
- [ ] 下游变量只重新分组正式上游变量时，仅说明分组关系与缺失传递，未重复上游已经完成的异常值清洗
- [ ] 可以由简短公式准确表达的计算关系已优先使用公式；公式输入、区间换算、权重和必要的非普通缺失条件均有正式依据
- [ ] 普通空白或没有记录后自然保留缺失的情况未机械写入 Criteria；只保留特殊编码、条件性缺失、汇总完整性、上游缺失传播或其它影响解释的缺失规则
- [ ] 连续变量的 `分类` 默认只写“连续变量”和单位；理论最大值、观察范围及极端值已放入 QA，除非范围本身属于正式定义
- [ ] 不同年份/Wave 的正式代码规则确有变化时，`定义逻辑` 已按周期分层陈述；没有规则变化时未机械拆期
- [ ] 普通单题重编码已直接写“题目含义 + 回答选项 + 赋值”，未机械添加“有效回答”；同一题义跨周期更换 raw 变量时，周期/来源对应已放在同一编号项的句末括号中，未另起来源编号
- [ ] 补充来源或回填规则已单独写清触发条件、赋值与其余处理，未与主问题赋值或来源对应混成一句
- [ ] Criteria 完整性术语按真实条件使用：多道问卷项目的作答完整性才写“有效回答”，合并或派生记录的完整性才写“有效记录”；“明确回答”“明确记录”命中均为 0
- [ ] 不知道、拒答、空白、不适用等特殊取值会影响结果时已直接写明处理；代码未筛除样本时未写“仅纳入……者”
- [ ] 若过程证据确认跨年份/Wave 存在同名不同义、同义不同名、raw 变量名或 File 演变，已放入 Criteria“注意点”，明确前后身份、适用周期与含义，并逐项 `<br>` 分行；未只写“题号发生变化”或无语义箭头；若无演变则不强行生成该块
- [ ] 原始矛盾专项默认为 `NOT_TRIGGERED`；只有用户给出口令“启用原始矛盾专项检查”时才比较指定定义变量及 raw 来源组，未将其作为每个主题的常规扫描
- [ ] 若专项已触发并发现客观矛盾，注意点已说明两个变量与来源组、每种矛盾方向及分类数量、总数和原始记录成因，并写明“保留原始矛盾，不做相互修正”；已复算的周期/来源/数量按 `<br>` 分行；未只写“存在 N 条矛盾组合”
- [ ] 已触发的原始冲突披露未使用“可能因此呈现不一致组合”“不用其中一组来源覆盖另一组”等模糊或工程化表述；未在缺少可靠复算时编造方向、数量或周期明细；派生关系或实际存在修正/覆盖时未误用该句式
- [ ] 同一 Criteria 句子未同时混写代码判定与衍生解释；需要同时说明时已拆入 `定义逻辑` 与 `注意点`
- [ ] Criteria 和公开 R 代码注释使用平实研究语言，不出现 `静默`、`路由` 等实现行话
- [ ] definition `Criteria` 必须使用 `criteria_heading()` / `criteria_item()` / `criteria_block()` 或同等源头结构化方式
- [ ] 变量名和代码对象使用反引号或 `<code>`；数据取值、编码值、分类值和问卷选项使用下划线加方括号
- [ ] detail / 组分概览按概念显式分组；每个概念显式 factor levels 固定 `source variables` 在前、`defined variables` 在后，多概念依次成对；未匹配变量归入 `Other / check` 并记录
- [ ] `### 1-提取变量` 的 `custom-textbox` 包含变量列表和 `Go to 提取变量` 按钮；占位符为 0，变量列表非空
- [ ] 笔记 detail / 组分概览部分只出现一个标准标题 `## 定义的组分概览`，旧标题壳为 0
- [ ] 最终 log 尾部包含 `Rscript exit code: 0`
- [ ] 正式目录只保留一个最终成功 log

## 执行线程自检

使用固定自检器：

```powershell
python <SKILL_ROOT>\scripts\check_definition_output.py `
  --formal-dir "<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}" `
  --raw-vars {{RAW_VARS_CSV}} `
  --analysis-db "{{ANALYSIS_DB}}" `
  --analysis-columns {{ANALYSIS_COLUMNS_CSV}} `
  --analysis-codebook "{{ANALYSIS_CODEBOOK}}" `
  --analysis-vars {{ANALYSIS_VARS_CSV}} `
  --forbid-vars {{FORBID_VARS_CSV}} `
  --log-prefix "{{LOG_PREFIX}}" `
  --require-log-exit-code
```

自检要求：

- [ ] 文件清单通过
- [ ] 禁止产物未出现
- [ ] raw/header/codebook 通过
- [ ] xlsx 维度与列名通过
- [ ] 变量前缀通过
- [ ] log 收口通过

## 目录结构检查

- [ ] 正式定义目录只包含正式交付物；未放过程卡、执行记录、工具自检 JSON、临时 QA、临时截图或 `.Rhistory`
- [ ] 过程卡、recover QA、工具自检 JSON、旧日志和临时材料均写入 `<DBCODEBOOK_HOME>\演示\定义\_执行线程\...`
- [ ] 公共规则、模板或工具修改只发生在本 Skill 的 `references`、`assets` 或 `scripts`
- [ ] 旧结构目录、旧草案和被替代材料已进入 `_执行线程` 下归档目录，不留在正式目录
- [ ] 未向 Codex 临时工作区写入过程材料；如出现，已清理并记录

## 证据链索引

本节只做索引，不写成长篇验收报告；用于让大脑和按需启动的独立验收任务快速定位证据。用户版笔记和 definition 只吸收必要背景解释，不承载完整内部证据链。

### 官方问卷详情 / bookapp 证据

- 截图路径：`{{BOOKAPP_SCREENSHOT_PATH}}`
- 页面路径：`http://localhost:8000/home/{{DATABASE_LOWER}}/`
- 目录路径：`{{BOOKAPP_PATH}}`
- 候选变量：`{{CANDIDATE_RAW_VARS}}`
- 最终 raw 变量：`{{RAW_VARS_CSV}}`
- 被排除变量及理由：
  - `{{EXCLUDED_VAR_1}}`：`{{EXCLUDED_REASON_1}}`

### 文献调研证据

- 检索记录或文献对照表：`{{LITERATURE_EVIDENCE_PATH}}`
- 主要官方材料/文献：`{{LITERATURE_SOURCES}}`
- 推荐方案：`{{LITERATURE_RECOMMENDATION}}`
- 未决差异及裁决：`{{LITERATURE_CONFLICT_DECISION}}`

### 下载 / 恢复证据

- transaction id 或 `--latest` 匹配结果：`{{TRANSACTION_OR_LATEST}}`
- recover QA 路径：`{{RECOVER_QA_PATH}}`
- `raw_data.csv`：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\raw_data.csv`
- `raw_codebook.csv`：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\raw_codebook.csv`

### 正式运行 / 自检证据

- 正式脚本：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\{{R_SCRIPT}}`
- 最终 log：`{{FINAL_LOG_PATH}}`
- 自检 JSON：`{{CHECK_JSON_PATH}}`

### 正式材料证据

- QA：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\{{QA_FILE}}`
- definition HTML：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\{{DEFINITION_HTML}}`
- detail HTML：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\{{DETAIL_HTML}}`
- 笔记：`<DBCODEBOOK_HOME>\演示\定义\{{DATABASE}}\{{TOPIC_ID}}_{{TOPIC_NAME}}\{{NOTE_MD}}`

### 裁决 / 异常验收判断

- 大脑或用户裁决摘要：`{{BRAIN_OR_USER_DECISION_SUMMARY}}`
- 机器证据是否存在失败、矛盾或无法解释的差异：`{{MACHINE_EVIDENCE_EXCEPTION}}`
- 是否仍有未裁决研究问题：`{{UNRESOLVED_RESEARCH_DECISION}}`
- 公共核心机制是否缺少足够 fixture / 回归边界：`{{UNBOUNDED_SHARED_MECHANISM_RISK}}`
- 用户或大脑是否明确要求独立验收：`{{EXPLICIT_VALIDATION_REQUEST}}`
- 是否送独立验收：`{{INDEPENDENT_VALIDATION_REQUIRED}}`
- 如已触发，验收任务与状态：`{{VALIDATION_THREAD_AND_STATUS}}`

## 本轮问题上报

执行中遇到新问题时，按以下规则处理，不能等最终成果完成后才含糊写一句。

- 阻断问题：立即暂停并回报大脑，不自行发明替代口径。
- 高复发机械问题：先解决当前任务，再在过程卡写明建议沉淀为流程/工具。
- 已知坑复发：必须升级为“流程未生效”，回传时单独列出，不得只当普通踩坑。
- 低复发小问题：记录在当前任务卡，可不进入通用流程。

### 新问题记录表

| 时间 | 问题 | 类型 | 是否已知坑复发 | 当前处理 | 建议沉淀 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## 回传与机器闭环

- 若触发变量候选闸门：回大脑线程，不下载 raw、不写正式 R。
- 正式成果完成后：完成 runner、固定自检、必要回归或复算、专项扫描和证据 manifest。
- 机器证据完整且无异常：以 `MACHINE_CHECK_PASS / COMPLETE` 完成并入账；不启动独立验收。
- 仅当机器证据冲突、研究问题未决、公共核心机制影响无法由回归界定，或用户/大脑明确要求时，才向独立验收任务发送限定范围问题包。
- 必须同时回传成果审核包和字段化踩坑复盘包；缺少任一包不视为完整收口。
- 机器闸门通过后即可更新索引/台账；只有实际启动异常验收时才等待其 PASS。宣传或下一主题仍由大脑另行派发。
