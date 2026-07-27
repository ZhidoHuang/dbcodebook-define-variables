# ELSA 数据库 profile

版本日期：2026-07-23

适用范围：ELSA 进入 `<DBCODEBOOK_HOME>\演示\定义` 固定定义工位后的数据库级身份、文件族、分析单位、缺失码、波次、样本与权重规则。它是数据库 profile，不替代本轮 bookapp 官方题目详情、下载后的 `raw_codebook.csv` 或大脑裁决。

## 1. 数据库基本信息

| 项目 | 当前规则 |
| --- | --- |
| 数据库 | ELSA（English Longitudinal Study of Ageing） |
| bookapp 入口 | `http://localhost:8000/home/elsa/` |
| 主个人标识 | `idauniq`；其标签跨波次表现为 unique individual serial number / unique cross-wave individual serial number / cross-wave identifier |
| household 标识 | 按波次识别，例如 `idahhw10`、`idahhw11`；IFS derived 还存在 `hhidw1` 等波次 household id |
| 当前 profile 状态 | 正式实跑版；已通过 ELSA 正式 raw 恢复、生成与机器闭环，具体主题仍须逐项核验来源身份、文件族和分析单位 |

## 2. 数据库主题参数

唯一参数源：

```text
<SKILL_ROOT>\references\database-theme-parameters.json
```

- ELSA `primary = #00773B`。
- CHARLS `primary = #A33842`，本轮不修改 CHARLS 的数据库主题色。
- 后续 ELSA definition HTML、公众号长图、封面、小红书及其它用户可见材料必须由数据库名读取该参数；禁止在任何主题脚本中单独手填 `#00773B`。
- 派生透明度、浅色背景或边框色由生成器从 `primary` 计算；不得另设主题级主色。
- ELSA definition HTML 的“周期分布”热图统一使用小写 `w1`、`w2`、…、`w11` 作为格内标签；摘要导读、Criteria 和其它正文仍使用完整写法 `Wave 1`、`Wave 2`、…、`Wave 11`。该缩写只用于空间受限的热图标签，不改写正式数据中的数值型 `wave`。

## 3. ELSA raw 身份：固定使用 Variable + File

### 3.1 身份键

- ELSA 的 raw 来源身份固定写为 `Variable (File)`。
- 判重、候选矩阵、标签、bookapp 批量输入、下载记录核对、raw 恢复、mapping 和 QA 均不得只按 `Variable`。
- 同名变量跨 File 不自动视为同一列，不自动拼接，也不自动选“看起来覆盖更多”的一条。

已核验例子：

- `palevel (Core data)`：Wave 3-5。
- `palevel (Derived Variables)`：Wave 2。
- `heacta/heactb/heactc (Core data)`：Wave 1-11。
- `heacta/heactb/heactc (COVID-19)`：COVID-19 Wave 2。
- `idauniq` 同时见于 Core、Index、Financial Derived、IFS Derived、Nurse、Wave 0、COVID-19、Life History、End of Life、HCAP、Nutrition、Pension Grid 等 File。

### 3.2 bookapp 与恢复工具格式

- 页面选择与过程材料统一使用 `Variable (File)` 表示来源身份。
- localhost transaction 的 ELSA `name` 若为 `variable (file)`，恢复工具需同时拆出 `variable` 和 `file` 传给 ELSA exporter。
- `--expect-vars` 仍核对页面导出的最终列名顺序；若两个来源最终显示名可能冲突，必须在下载前回大脑裁决 rename，不得让工具静默覆盖。
- ELSA 唯一 ID 文件导出的 raw header 固定按 `ID, idauniq, <selected variables...>` 核验；不得套用 CHARLS 的 `ID, id, year`。
- ELSA 正式 db/analysis 身份列固定为 `ID, idauniq, wave`。`wave` 只在正式 R 中从 `ID` 的 `Wave <n>_` 前缀解析，不改写 raw。
- ELSA `raw_codebook.csv` 中，`Variable (File)` 是来源与 mapping/证据身份；`newname` 是 `raw_data.csv` header 和 R 读取的导出列身份。两者必须同时保留、逐行对应。
- ELSA codebook 对账使用 `newname` 与 expected/raw header 精确匹配；禁止先把 `Variable` 去掉 `(File)`，再用裸变量名替代 `newname` 做 QA。
- `newname` 不得为空、重复、缺少预期变量或出现 header 外的意外变量。
- 固定产物自检器必须显式传 `--db elsa`，并同时传完整 `--raw-vars`；ELSA 模式按 `ID, idauniq` 与 `newname` 对账，不得依赖默认 CHARLS 身份模式或省略 raw 检查。

## 4. 文件族边界

下列文件族只描述边界，不表示默认合并：

| 文件族 | 边界 | 默认分析单位/风险 |
| --- | --- | --- |
| Core data | 主纵向访谈框架；包含主访谈变量，也可能包含 self-completion outcome、派生变量和 copied/整理字段 | 通常以个人-波次为入口，但仍要核对 `idauniq`、wave、访谈结果与变量适用对象 |
| Self-completion | 自填问卷与主访谈不同响应机制；Core/Index 中可能只出现 outcome，Life History 也可出现 self-completion 字段 | 不能把 self-completion 缺失当主访谈未回答；先确认问卷是否发放/回收 |
| Nurse data / health visit | 护士访视、体测与生物指标；仅特定波次和访视成功对象 | 以护士访视记录为界；不能用 Core 全体分母解释覆盖率 |
| Derived Variables | 官方派生文件；同名变量可能与 Core 中整理版并存 | 必须记录公式、来源波次、覆盖和版本；不能因为官方派生就自动采用 |
| IFS Derived Variables / Financial Derived Variables | 外部/官方整理分析文件，包含复制变量、权重、经济和样本派生 | 来源字段和复制关系要追溯；不能与 Core 同名变量只按名字合并 |
| Harmonised ELSA | 跨数据库协调口径，不等于原始 ELSA 文件 | 只有用户/大脑明确选择 harmonised 路线时使用；不得与 Full ELSA raw 混做一个定义 |
| Wave 0 | HSE predecessor/基线补充体系，包含 Wave 0 Common 与 Wave 0 Additional | 题期、回忆窗、变量体系与 ELSA Wave 1+ 不同；默认单列候选，不自动拼入纵向主线 |
| COVID-19 | COVID 专题波次；页面使用 COVID-19 Wave 1/2 | 即使变量名与 Core 相同，也必须按 `Variable (COVID-19)` 独立处理 |
| Life History data | 回顾性生命历程访谈 | 不是常规当期波次测量；有独立 outcome 与 `retrowgt` |
| End of Life data | 对已故样本的代理/末期访谈 | 记录对象与答题人可能不同；不能当在世本人 Core 访谈 |
| HCAP Respondent / HCAP Informant | 认知专题受访者与知情人文件 | respondent/informant 分开；同一 `idauniq` 不表示同一答题人记录 |
| Nutrition data / Nutrition data detail | 营养专题；detail 可能一人多行 | 先确认行级单位和 detail key，禁止按 `idauniq` 去重 |
| Pension Grid data | pension-level grid；页面明确使用 `penid` 作为 cross-wave pension identifier | 一人可多养老金记录；分析单位通常是 pension record，不是个人 |
| Index file data | outcome、productive/issued 状态和跨波次索引 | 用于界定样本/访谈状态，不自动当主题测量值 |

## 5. ID、成员与重复记录

### 5.1 个人与 household

- `idauniq` 是跨波次个人入口，不等于任何 File 中都唯一。
- `ID` 是 bookapp 合并后的个人-波次行键；正式阶段必须检查 `ID` 无重复。
- `wave` 从 `ID` 前缀解析，例如 `Wave 1_100035` 解析为 `1`。所有 `ID` 必须成功解析，且本主题只允许 `wave` 为 `1:11`；出现其它真实格式必须停回大脑，不得猜补。
- 同一 `idauniq` 可跨 `wave` 重复，这是 ELSA 纵向结构；不得按 `idauniq` 去重。
- household id 是波次化身份；不得把 `idahhw10`、`idahhw11` 或 `hhidw*` 当稳定跨波次 household id。
- partner 身份需用当前波次成员状态和 partner id 核对；IFS Derived 中已见 `idauniq_p`。

### 5.2 core members、partners 与 refreshment sample

- `sampsta`、`samptyp`、`corepartner` 等分别覆盖不同波次/文件；不能用单一变量概括全部波次。
- Core members、core partners、younger/new partners 的纳入边界必须由研究问题与权重共同裁决。
- refreshment sample 是样本来源，不是波次覆盖；已见 `refreshtype (IFS Derived Variables)`。
- “有该波次记录”“属于 core member”“属于 partner”“来自 refreshment sample”“有可用权重”是五个不同判断。

### 5.3 proxy、household/copy values

- proxy 访谈必须显式识别；已见 `proxy (IFS Derived Variables)`。
- household 一人回答后复制给成员、partner 提供、官方 copied variable、以及本人回答是不同证据层级。
- IFS Derived 中存在 `sex`、`age`、`wgt` 等 `copy of ...` 字段；mapping 必须追溯到被复制的来源变量，不能只停在 copied 列。
- 用户若要求“本人回答”，proxy/copied 值不得默认混入；用户若允许家庭共享值，也要在 Criteria/QA 披露。

### 5.4 重复 ID 文件

- `Nutrition data detail` 与 `Pension Grid data` 在 bookapp 页面逻辑中属于重复 ID 文件，下载与预览按 File 分组。
- HCAP Informant、End of Life、grid/detail 或其它专题文件也必须实际检查 `idauniq` 重复与附加 key。
- 禁止用 `distinct(idauniq, .keep_all = TRUE)` 解决重复；必须先定义分析单位和排序/聚合规则，并回大脑裁决。

## 6. 缺失码与编码规则

- ELSA 负值缺失码必须按 `Variable (File)`、wave、codebook/问卷逐项解释。
- 禁止套用 CHARLS 的 `997/998/999` 或任何 ELSA 全库统一负值字典。
- 同一负值在不同文件/题目可代表 not applicable、refused、don't know、not asked、not issued、proxy/copy 等不同状态。
- 候选阶段只记录页面可见取值；正式阶段在下载后逐项对照 `raw_codebook.csv` 和 raw 分布。
- 数值、时长、频率、权重、总分、日期等变量在解释完负值前不得参与计算。

## 7. 波次、适用对象、样本与权重

- 波次覆盖：变量在哪些 Wave/File 出现。
- 适用对象：谁被问到或谁有资格进入该模块。
- refreshment sample：样本何时/以何种来源进入研究。
- 权重：为哪类对象、哪种访视、横断面或纵向估计服务。
- 四者不得互相替代；“有 Wave 1-11”不等于全体对象、也不等于同一权重可跨波次使用。

已核验的权重差异例子：

- `wgt (IFS Derived Variables)`：cross-sectional weight（copy of `wxwght`）。
- `lwgt`：Wave 1 baseline longitudinal weight。
- `l4wgt`：Wave 4 baseline longitudinal weight。
- COVID-19 `wtfin1`：core members；`wtfin2`：core members & partners。
- Life History `retrowgt`：life-history interview weight。

权重选择属于大脑裁决点；执行线程只能提供候选、对象、波次与用途证据。

## 8. ELSA 主题开工闸门

每个主题正式下载前必须回传：

1. `Variable (File)` 候选矩阵。
2. 分文件/波次题干、取值、适用对象和 raw/derived 身份。
3. 同名跨 File/波次差异。
4. analysis unit、core/partner/proxy/copied、refreshment、weight 风险。
5. 可选定义方案与事实推荐。

涉及变量范围、Variable+File 身份、数据文件族、分析对象、权重、编码、跨波次语义或 raw 重下时，必须暂停并回大脑裁决。
