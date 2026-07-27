library(jsonlite)

skill_root <- Sys.getenv("DBCODEBOOK_SKILL_ROOT", unset = "")
if (nzchar(skill_root)) {
  script_dir <- file.path(skill_root, "scripts", "tests")
} else {
  script_argument <- grep(
    "^--file=",
    commandArgs(trailingOnly = FALSE),
    value = TRUE
  )
  if (length(script_argument) > 0) {
    script_file <- sub("^--file=", "", script_argument[[1]])
  } else {
    source_file <- tryCatch(sys.frame(1)$ofile, error = function(error) NULL)
    if (is.null(source_file)) {
      stop(
        "Cannot determine the test script location. Set DBCODEBOOK_SKILL_ROOT.",
        call. = FALSE
      )
    }
    script_file <- source_file
  }
  script_dir <- dirname(normalizePath(script_file, winslash = "/", mustWork = TRUE))
}
eval(parse(
  file = file.path(script_dir, "..", "summary_fact_helpers.R"),
  encoding = "UTF-8"
))
eval(parse(
  file = file.path(script_dir, "..", "render_definition_bundle.R"),
  encoding = "UTF-8"
))

expect_identical <- function(name, actual, expected) {
  if (!identical(actual, expected)) {
    stop(name, " failed. expected: ", expected, "; actual: ", actual)
  }
  list(name = name, expected = expected, actual = actual, ok = TRUE)
}

expect_error_contains <- function(name, expression, expected) {
  message <- tryCatch(
    {
      force(expression)
      ""
    },
    error = function(error) conditionMessage(error)
  )
  if (!grepl(expected, message, fixed = TRUE)) {
    stop(name, " failed. expected error containing: ", expected, "; actual: ", message)
  }
  list(name = name, expected = expected, actual = message, ok = TRUE)
}

charls_periods <- c(2011L, 2013L, 2015L, 2018L, 2020L)
mixed_charls <- data.frame(
  period = charls_periods,
  nonmissing = c(90L, 80L, 90L, 80L, 80L),
  total = rep(100L, 5),
  rate = c(0.90, 0.80, 0.90, 0.80, 0.80)
)
all_high <- data.frame(
  period = c(2011L, 2013L),
  nonmissing = c(85L, 95L),
  total = c(100L, 100L),
  rate = c(0.85, 0.95)
)
multiple_low_groups <- data.frame(
  period = c(1L, 2L, 3L),
  nonmissing = c(90L, 80L, 60L),
  total = c(100L, 100L, 100L),
  rate = c(0.90, 0.80, 0.60)
)

note_order_fixture <- compose_definition_note_lines(
  summary_section = "SUMMARY",
  definition_html_lines = c("DEFINITION_START", "DEFINITION_END"),
  reference_lines = c("> 1、REFERENCE_ONE", "> 2、REFERENCE_TWO"),
  extract_box = "EXTRACT",
  publish_code = "CODE",
  detail_html_lines = "DETAIL"
)
summary_section_fixture <- render_summary_note_section(
  entry = list(parts = list("目录说明。")),
  selection = list(
    raw_count = 1,
    concepts = "测试变量",
    final_count = 1
  ),
  summary_rows = "| `test_var` | 测试变量 | 1 | 全周期 | 全样本 |",
  theme_color = "#A33842"
)
summary_table_range_fixture <- attr(
  summary_section_fixture,
  "summary_table_range",
  exact = TRUE
)
definition_end_position <- match("DEFINITION_END", note_order_fixture)
reference_one_position <- match("> 1、REFERENCE_ONE", note_order_fixture)
reference_two_position <- match("> 2、REFERENCE_TWO", note_order_fixture)
materials_position <- match("## 材料", note_order_fixture)

checks <- list(
  expect_identical(
    "CHARLS five-year full coverage",
    summary_period_text(charls_periods, "", charls_periods),
    "全周期"
  ),
  expect_identical(
    "CHARLS mixed high and low coverage",
    summary_object_text(mixed_charls, prefix = ""),
    "2011、2015 全样本；<br>2013、2018、2020 约 80% 样本"
  ),
  expect_identical(
    "ELSA partial waves",
    summary_period_text(c(2L, 4L), "Wave", 1:5),
    "Wave 2、Wave 4"
  ),
  expect_identical(
    "CHARLS observed subset is not full cycle",
    summary_period_text(c(2011L, 2013L, 2015L, 2018L), "", charls_periods),
    "2011、2013、2015、2018"
  ),
  expect_identical(
    "all periods at least 85 percent",
    summary_object_text(all_high, prefix = ""),
    "全样本"
  ),
  expect_identical(
    "multiple low coverage groups",
    summary_object_text(multiple_low_groups, prefix = "Wave"),
    "Wave 1 全样本；<br>Wave 2 约 80% 样本；<br>Wave 3 约 60% 样本"
  ),
  expect_identical(
    "insight inline code rendering",
    summary_render_inline_code("变量 `da005` 进入定义。"),
    "变量 <code>da005</code> 进入定义。"
  ),
  expect_identical(
    "summary table start is exposed structurally",
    summary_section_fixture[summary_table_range_fixture[["start"]]],
    "| 定义变量 | 含义 | 组成 | 覆盖周期 | 对象 |"
  ),
  expect_identical(
    "summary table end is exposed structurally",
    summary_section_fixture[summary_table_range_fixture[["end"]]],
    "| `test_var` | 测试变量 | 1 | 全周期 | 全样本 |"
  ),
  expect_error_contains(
    "insight literal code tag rejected",
    summary_validate_insight_inline_code("变量 <code>da005</code> 进入定义。"),
    "不要手写 <code> 标签"
  ),
  expect_error_contains(
    "insight unmarked variable rejected",
    summary_validate_insight_inline_code("变量 da005 进入定义。"),
    "变量名必须使用成对反引号：da005"
  ),
  expect_identical(
    "references follow the complete definition table",
    reference_one_position > definition_end_position,
    TRUE
  ),
  expect_identical(
    "references precede materials",
    reference_two_position < materials_position,
    TRUE
  ),
  expect_identical(
    "references have one blank line above",
    note_order_fixture[reference_one_position - 1L],
    ""
  ),
  expect_identical(
    "references remain contiguous",
    reference_two_position,
    reference_one_position + 1L
  )
)

report <- list(ok = TRUE, checks = checks)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 1 && nzchar(args[1])) {
  write_json(report, args[1], pretty = TRUE, auto_unbox = TRUE)
}
cat("summary helper fixtures PASS\n")
