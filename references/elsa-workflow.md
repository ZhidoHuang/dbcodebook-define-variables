# ELSA 变量定义标准流程

版本日期：2026-07-27

适用范围：通过 bookapp 为 ELSA 建立候选、经大脑裁决后下载 raw、编写正式 R 定义，并生成 xlsx、QA、HTML、笔记、日志、自检与过程卡。

本流程只定义 ELSA 执行骨架。数据库身份和文件族见 `ELSA数据库profile.md`；通用 R 与用户材料见 `dbCodeBookr函数与用户材料规范.md`。禁止从 CHARLS 流程复制变量名、题号、波次、特殊编码、主题经验、前缀或权重。

## 1. 目录与角色

- 正式数据库根：`<DBCODEBOOK_HOME>\演示\定义\ELSA\`。
- 过程根：`<DBCODEBOOK_HOME>\演示\定义\_执行线程\ELSA\`。
- 正式主题目录：`<DBCODEBOOK_HOME>\演示\定义\ELSA\<主题编号>_<主题名>`，只在候选裁决后按大脑授权创建。
- 过程主题目录：`<DBCODEBOOK_HOME>\演示\定义\_执行线程\ELSA\<主题编号>_<主题名>`。
- 机器闭环通过前，执行任务不得修改索引或验收台账；通过后只原位更新本主题记录。执行任务不得修改宣传资产，也不得启动未派发主题。

正式成果完成后由执行任务完成机器闸门并直接闭环入账。独立验收不属于常规步骤，只在机器证据冲突、研究问题未决、公共核心机制影响无法由回归界定，或用户/大脑明确要求时启动。候选闸门仍只回传来源大脑任务。

## 2. 开工必读顺序

1. `<SKILL_ROOT>\references\project-governance.md`
2. `<SKILL_ROOT>\references\directory-structure.md`
3. `<DBCODEBOOK_HOME>\演示\定义\_索引\主题索引.md`
4. `<DBCODEBOOK_HOME>\演示\定义\_索引\定义验收台账.md`
5. `<SKILL_ROOT>\references\elsa-workflow.md`
6. `<SKILL_ROOT>\references\elsa-profile.md`
7. `<SKILL_ROOT>\references\user-material-rules.md`
8. `<SKILL_ROOT>\assets\current-task-template.md`

CHARLS Skill/流程只用于辨认可复用的任务卡、证据链、正式/过程目录分离、R runner、自检与验收骨架；不得作为 ELSA 数据事实来源。

### 2.1 新主题与已有主题更新分流

- 新主题，或本轮需要改变 raw 范围、`Variable (File)` 来源、文件族、分析单位、权重、编码、跨 Wave 含义或 transaction 时，必须完整执行候选闸门、裁决、页面选择、下载与 recover。
- 已有正式主题仅更新摘要导读、`Criteria`、公开 R 呈现、HTML 或笔记结构，且 raw、transaction、来源身份、变量集合、正式口径和数值均不改变时，直接使用当前正式 R、`raw_data.csv`、`raw_codebook.csv` 和已确认裁决重建；不得为形式迁移重复下载或重新裁决。
- 已有主题更新时，用户文本初稿只依据当前正式业务代码、raw 标签、正式 codebook 和明确裁决组织。旧 `Criteria`、旧笔记和旧 HTML 只能在初稿完成后用于查漏与业务回归，不作为权威事实源，也不计算句子重合率、改写率或“旧句复用为零”。
- 新主题附带用户既有 R、zip、工作簿、笔记或其它历史材料时，先按本流程独立完成 dbCodeBook 探索与候选初稿；历史材料只能在初稿完成后用于查漏、比较和识别潜在风险，不得作为候选发现入口、当前事实来源或措辞底稿。历史材料与当前页面、官方材料或实际 raw 不一致时，以当前证据形成待裁决项，不得静默沿用旧做法。
- 更新过程中一旦发现现有来源证据无法支持当前口径，或出现新的候选、含义冲突及文件族风险，立即退出更新分支并回到候选闸门。

## 3. bookapp 候选阶段

页面：`http://localhost:8000/home/elsa/`。

### 3.1 必须使用真实浏览器

- 新开或接管干净标签，先从页面目录进入相关节点；目录面板筛选词只用于定位目录。需要发现跨目录候选时再执行普通检索，并单独记录普通检索关键词与结果。
- 先查目录节点，再查英文/中文同义词；记录 0 结果同样是证据。
- 启用页面 `Label` 字段，核验原题/波次文本；Easy label 只作入口。
- 逐项记录 `Variable (File)`、Wave、目录/数据家族、题干、页面可见取值、适用对象、raw/derived、波次差异、排除理由和截图路径。
- 不通过旧代码、本地导出、底层 DB、Parquet 或缓存发现候选。
- 新主题从第一次网页操作起同步建立 `definition_search_record.json`，结构使用 `<SKILL_ROOT>\assets\retrieval-record-template.json`。`exploration_log` 按实际发生顺序记录目录进入、普通检索、页面观察、下一步决定与理由；`candidate_decisions` 记录候选纳入、排除和依据步骤。不得在候选已经确定后根据旧代码、变量名或最终结果反编检索路径。
- 每个正式候选必须对应一个已记录的 `Variable (File)` 来源组、真实发现步骤和纳入理由。来源记录不完整时，候选不得进入下载。

### 3.2 针对性文献调研

完成 dbCodeBook 目录/普通检索、官方题目详情核对并形成初步候选后，在变量选择与下载之前进行针对性文献调研。文献用于比较既有 ELSA 研究如何界定和构造同一研究概念，不能替代官方题目、实际 raw、`raw_codebook.csv` 或文件身份。

证据优先级固定为：

1. dbCodeBook 官方题目详情、实际 raw 取值与 `raw_codebook.csv`。
2. ELSA 官方用户指南、问卷、技术文档、派生变量说明和可定位构造过程的 Harmonised ELSA 技术代码本。
3. 原始量表或方法文献、正式指南、共识文件、法律政策和主管机构文件。
4. 在研究设计、变量构造和报告完整性上可靠，且明确给出可复核 ELSA 题项、raw、公式或计分的同行评议研究。
5. 一般应用研究和研究惯例。

执行要求：

- 所有新定义至少完成一次与主题直接相关的定向检索；简单单题可简要确认是否存在不同的常见定义。
- 量表、认知测验、总分、指数、复合变量，以及存在多种常见构造、跨 Wave 项目变化或计分歧义的主题，必须进行实质文献调研。
- 同行评议和期刊发表本身不等于权威定义。必须按来源直接性、期刊与栏目质量、研究设计、变量构造完整性、题项/周期/公式可复核程度和结论边界评价文章；一般应用研究只能作为使用实例，不能替代官方材料或原始方法来源。
- 官方材料已足以确定题义和构造时，不为增加引用数量而补普通应用论文。正式笔记优先保留官方、技术、原始方法、正式指南或主管机构来源；一般应用论文默认只进入过程对照。
- 记录文献或官方材料、使用 Wave/样本、研究概念、纳入项目或 raw（如有）、公式或计分、取值范围、缺失/完整性处理，以及与本轮候选的异同。
- 每项实际采用的关键官方或方法来源在过程目录保留可独立阅读的 Markdown 证据正文，分别说明“来源明确陈述”“根据官方题目/raw 可直接核实”“本轮拟采用方案”。不能只在汇总表中写“支持本定义”。
- 文献未报告 raw、计分或缺失细节时，明确记为“未报告”，不得根据结果或上下文反推。
- 文献之间，或文献与官方题目、实际 raw 之间不一致时，形成候选方案并回大脑/用户裁决，不得自行选择最常见方案。
- 文献证据默认留在过程证据和候选包；只有会改变变量含义、可比性或解释边界的结论，才按公共用户材料规则转写到摘要、`Criteria` 或注意点。

### 3.3 主题独立性、命名与 Wave 完整性

正式分配主题范围、变量名和下载清单前，必须完成：

1. **既有成果查重**：对照现有 ELSA 分析变量的研究含义、`Variable (File)` 来源、构造逻辑和实际取值。逐值相同或只换名称的变量直接复用；仅为已有变量做简单合并、比例或二分类时，优先并入原主题。
2. **主题边界判断**：一个候选包包含多个独立研究概念时，明确选择合并成组合主题还是拆分主题，并记录理由。用户明确指定组合主题时可以合并，但不能由旧 R 的变量清单自动决定。
3. **命名系列检查**：命名前检查现有 ELSA 正式变量是否已有同一概念系列；有系列关系时复用共同前缀。不得机械继承 CHARLS 的 `A_` 前缀，也不得因为历史参考代码已有名称就跳过命名裁决。
4. **Wave 完整性回查**：按研究概念列出预期 Wave、实际 `Variable (File)` 来源和题义。前后 Wave 有来源而中间 Wave 缺失，或同一来源出现异常断层时，必须回到目录和普通检索继续核对；未解释的断层不得通过批量合并、优先级或 `coalesce` 掩盖。
5. **按 Wave 评估可用记录**：分别报告每个候选变量的适用对象、非缺失人数和覆盖率；不得仅用全部人次或所有 Wave 合并后的总行数判断可用性。

候选结论使用 `NEW`、`MERGE`、`REUSE` 或 `DEFER`。只有 `NEW` 且研究口径已经裁决时，才进入正式下载与生成。

### 3.4 ELSA 身份闸门

- 候选、判重、mapping、下载标签和 QA 的身份键均为 `Variable + File`。
- 同名 Variable 跨 File 必须拆行；例如 `palevel (Core data)` 与 `palevel (Derived Variables)`。
- Core 与 COVID、Wave 0、Nurse、Life History、End of Life、HCAP、Nutrition、Pension Grid、Harmonised ELSA 不得只按同名变量拼接。

### 3.5 候选闸门触发条件

以下任一出现，执行线程必须停在候选阶段并主动回传来源大脑任务：

- 变量范围或主题含义存在多种合理口径。
- 同名 Variable 跨 File 或数据家族。
- raw 与官方 derived 可二选一。
- 分析对象涉及 core member、partner、proxy、copied value、refreshment sample。
- 分析单位可能不是个人-波次，或同一 `idauniq` 多行。
- 权重、负值编码、跨波次语义、Wave 0/COVID/Harmonised 是否纳入需裁决。
- 需要重新下载 raw 或改变 transaction。

候选包至少包含：同步形成的 `definition_search_record.json`、候选矩阵、文献或官方定义对照、主题独立性与命名结论、Wave 完整性与可用记录、方案比较、事实推荐、待裁决问题、证据链索引、已知坑/新增坑。回传后暂停；不得下载 raw、创建正式主题目录、写正式 R 或生成正式材料。

## 4. 大脑裁决后的正式阶段

仅在收到明确裁决后执行：

1. 按裁决固定 `Variable (File)` 清单、rename、分析对象、波次、权重和编码边界。
2. 在 bookapp 页面重新确认标签、预览、header、记录数和文件分组。
3. 在执行 recover 前即时保存正式 bookapp 证据到过程目录：完整选择列表截图；存在多个 File 时的 File/Wave 覆盖截图；正式预览的 header、记录数和变量数截图。截图后立即验证每个文件真实存在、大小大于 0 且可解码；不得只在过程卡或送验文字中预写路径。
4. 点击下载生成本次 transaction。
5. localhost 使用 `recover_bookapp_export.py --db elsa --latest` 恢复本次 zip/raw；只有 latest 无法匹配才回退明确 transaction，并记录原因。
6. 恢复工具必须按 ELSA `Variable (File)` 拆分 `variable` 与 `file`；QA 必须确认 transaction、header、codebook 和文件列表。
7. ELSA raw header 按 `ID, idauniq, <selected variables...>` 精确核验；不能期待或伪造 CHARLS 的 `id/year`。
8. ELSA codebook 同时核验两层身份：`Variable (File)` 保留来源/mapping 证据，`newname` 与 raw header/expected vars 精确匹配；不得 normalize 掉 File 后用裸 Variable 对账。
9. `newname` 为空、重复、缺少预期变量或出现 header 外意外变量时，恢复必须失败。
10. 才可创建正式主题目录、编写唯一正式 R 脚本并运行。

## 5. raw 与分析单位核验

正式定义前逐项确认：

- `idauniq` 是否唯一；若不唯一，附加 key 与一行代表什么。
- 正式 db/analysis 身份列固定为 `ID, idauniq, wave`；raw 保持下载原貌。
- `wave` 由正式 R 从 `ID` 的 `Wave <n>_` 前缀解析；所有 `ID` 必须成功解析，`wave` 只能为 `1:11`，`ID` 必须唯一。
- `idauniq` 允许跨 `wave` 重复；这是个人纵向记录，禁止按 `idauniq` 去重。
- wave/year 字段来自何处，是否混入 COVID/2023 等特殊期。
- household id 是否波次化。
- core member、partner、proxy/copy、访谈 outcome、refreshment sample。
- File 是否属于重复 ID 的 nutrition detail、pension grid 或 respondent/informant/代理结构。
- 权重的对象、基线、横断面/纵向用途与波次。
- 每个 raw 变量全部负值及官方解释；禁止套用 CHARLS 特殊码。

任何一项会改变研究对象或正式口径时，停回大脑。

### 5.1 重叠来源一致性闸门

- 当两个或多个 `Variable (File)` 来源在部分 Wave 重叠，而正式路线只采用其中一个来源时，必须在重叠 Wave 对同一概念逐项逐行比较。
- 过程证据必须为每项分别记录：重叠周期总行数、双方非空可比较行数、双方同时缺失行数、缺失模式 mismatch、有效值 mismatch，以及最终来源选择理由。禁止只写笼统的 overlap rows + mismatch，也不能只比较总频数或列名。
- mismatch 为 0 才可按已裁决路线继续；mismatch 大于 0 必须暂停并回传大脑裁决，不得自行用优先级或 `coalesce` 掩盖差异。
- 该闸门适用于所有跨 File/Wave 来源拼接，不限某一主题。

## 6. R、输出与用户材料

- 通用包头、`dbCodeBookr`、公开代码边界、mapping、xlsx、QA、runner 和自检遵守 `dbCodeBookr函数与用户材料规范.md` 与 current task。
- 笔记摘要导读与 `Criteria` 的内容、语言和栏目职责统一遵守 `dbCodeBookr函数与用户材料规范.md` 中的“用户自由文本公共规则”；ELSA 不维护第二套读者版语言规则。
- ELSA 只补充数据库身份键、`Wave` 周期标签、完整 `Variable (File)` 来源身份、逐项核实的 ELSA 缺失码和数据库特定分类编码。
- 正式分类变量默认保留规范化后的英文/ASCII 标签；只有 YES/NO 二分类默认用 `1/0`。频率、等级、状态等非 YES/NO 多分类不得为了排序便利自行改成 `0-3` 等数值编码。
- recover QA 与固定自检器已负责 raw header、codebook `newname`、空值、重复和意外列等工程检查；这些重复校验不塞入 `# 输出` 之前的读者版 R 主线。正式变量生成必需的身份转换（例如从 `ID` 生成 `wave`）保留简洁中文注释；wave 范围、ID 重复、idauniq 缺失等完整性闸门放在 `# 输出` 后的内部 QA/自检区。
- ELSA 的变量范围、命名/前缀、总分/总量和数据库特定缺失处理仍由本主题裁决；不得机械继承 CHARLS 的数据库事实。
- mapping 必须追溯到 `Variable (File)` 原始来源；同名跨 File 在内部证据与 QA 中不可丢失 File。
- 用户可见 HTML 主题色从 `数据库主题参数.json` 按 `ELSA` 读取 `#00773B`，禁止逐主题手填。
- ELSA detail / 组分概览宽表的波次列必须在进入 `generate_html_definition_long()` 前显式命名为 `Wave 1`、`Wave 2`……`Wave N`，不得保留裸数字列名。这样生成器才能把 `original_vars`、`easylabel` 等辅助信息放在周期列之前，并按 Wave 数字顺序展示周期列。
- 正式用户材料只写研究对象、变量语义、波次/来源差异与分析影响，不写 transaction、recover、自检、验收或工具史。

## 7. 机器闭环与按需异常验收

正式成果完成后：

1. 使用正式 runner 从头运行同一份正式 R，保留一个成功日志和退出码。
2. 使用固定自检器核对文件清单、raw/header/codebook、xlsx、analysis 列、禁止产物和日志；ELSA 调用必须显式传 `--db elsa`，并完整传入 `--raw-vars`、`--analysis-columns`、`--analysis-vars`、`--forbid-vars` 等参数，不得省略 raw 检查。
3. 过程卡补齐 `## 证据链索引`、已知坑回顾和字段化新增坑。
4. 在过程目录生成 `validation_evidence_manifest.json`（或等价机器可读清单），枚举本任务引用的全部截图、recover QA、固定自检、正式成功日志和关键对照报告。每项记录绝对路径、`exists`、`size`、`readable`；图片还必须记录 `decodable`。任一引用证据不存在、大小为 0、不可读或图片不可解码时，机器闸门不得通过。
5. manifest 和其它过程证据只能放过程目录，不得进入正式主题目录。
6. 机器证据完整且一致时，状态改为 `MACHINE_CHECK_PASS / COMPLETE`，更新索引/台账并回传大脑。
7. 只有机器证据冲突、研究问题未决、公共核心机制边界不足或用户/大脑明确要求时，才向独立 ELSA 验收任务发送限定范围问题包；普通机械返修由执行任务自行闭环。
8. 过程卡状态按实际路径同步：默认路径为 `MACHINE_CHECK_PASS / COMPLETE`，入账后为 `CLOSED / INDEXED`；实际启动异常验收时才使用 `SENT_FOR_VALIDATION`、`RESENT_FOR_VALIDATION`、`VALIDATION_PASS`。
9. 机器闸门通过前不得改索引/台账、不得自称完成、不得启动宣传；实际启动异常验收时才等待其 PASS。

## 8. 工具边界

`<SKILL_ROOT>\scripts\recover_bookapp_export.py` 当前静态检查已包含：

- `source == "elsa"` 时调用 `export_elsa_data`。
- ELSA/CRELES transaction name 按 `Variable (File)` 拆分为 `variable` 与 `file`。
- supported 列表包含 `elsa`。

这只表示结构上支持 ELSA，不等于已完成 ELSA 实跑。首次正式下载仍需在候选裁决后做受控恢复 QA；若 header、File 拆分或重复 ID 文件分组异常，先回大脑，不自行修改 bookapp。

### 8.1 spreadsheet 可选渲染边界

- `openxlsx` 成品与通用 artifact-tool 可能出现 OpenXML `PartDoesNotExist` 兼容问题，当前视为已知的可选渲染工具问题；未来修复另立工具任务。
- 固定自检、R 直接重读和独立逐行复算均通过时，可选视觉渲染不得阻断定义验收，也不要在每个主题反复尝试 normalized 副本、截图渲染或样式试验。
- 这一边界不降低 xlsx 核验要求：文件可打开性、sheet、行列数、列名、关键值分布和与正式分析结果的一致性仍必须由固定自检、R 重读或等价独立核验覆盖。
