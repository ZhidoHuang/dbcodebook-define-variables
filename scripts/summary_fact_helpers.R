# 摘要导读五列表的公共事实生成函数。
# “含义”和概念分组由主题人工提供；变量集合、顺序、来源数、覆盖周期和对象均从正式产物推导。

summary_split_sources <- function(x) {
  values <- trimws(unlist(strsplit(ifelse(is.na(x), "", x), ",\\s*")))
  unique(values[nzchar(values)])
}

summary_period_ranges <- function(periods, prefix = "Wave") {
  periods <- sort(unique(as.integer(periods)))
  if (length(periods) == 0) return(character())
  breaks <- c(1, which(diff(periods) != 1) + 1, length(periods) + 1)
  vapply(seq_len(length(breaks) - 1), function(i) {
    values <- periods[breaks[i]:(breaks[i + 1] - 1)]
    if (length(values) == 1) {
      if (nzchar(prefix)) paste(prefix, values) else as.character(values)
    } else {
      if (nzchar(prefix)) {
        paste0(prefix, " ", values[1], "-", values[length(values)])
      } else {
        paste0(values[1], "-", values[length(values)])
      }
    }
  }, character(1))
}

summary_period_text <- function(periods, prefix = "Wave", all_periods = NULL) {
  periods <- sort(unique(as.integer(periods)))
  if (!is.null(all_periods) && identical(periods, sort(unique(as.integer(all_periods))))) {
    return("全周期")
  }
  paste(summary_period_ranges(periods, prefix), collapse = "、")
}

summary_object_text <- function(period_stats,
                                threshold = 0.85,
                                split_gap = 0.20,
                                prefix = "Wave") {
  if (nrow(period_stats) == 0) stop("摘要变量没有任何非缺失覆盖周期。")
  rates <- period_stats$rate
  if (all(rates >= threshold)) return("全样本")

  low <- period_stats[rates < threshold, , drop = FALSE]
  high <- period_stats[rates >= threshold, , drop = FALSE]
  parts <- character()
  if (nrow(high) > 0) {
    parts <- c(parts, paste0(summary_period_text(high$period, prefix), " 全样本"))
  }
  if (nrow(low) > 0) {
    rounded <- round(low$rate * 10) * 10
    percentages <- sort(unique(rounded), decreasing = TRUE)
    low_parts <- vapply(percentages, function(percent) {
      periods <- low$period[rounded == percent]
      paste0(summary_period_text(periods, prefix), " 约 ", percent, "% 样本")
    }, character(1))
    parts <- c(parts, low_parts)
  }
  paste(parts, collapse = "；<br>")
}

build_summary_facts <- function(analysis_db,
                                analysis_codebook,
                                meanings,
                                groups,
                                meaning_reviewed,
                                source_identity = NULL,
                                period_col = "wave",
                                expected_periods = NULL,
                                threshold = 0.85,
                                split_gap = 0.20,
                                period_prefix = NULL) {
  required_codebook <- c("Variable", "original_vars", "Label")
  missing_codebook <- setdiff(required_codebook, names(analysis_codebook))
  if (length(missing_codebook) > 0) {
    stop("analysis_codebook 缺少摘要事实列：", paste(missing_codebook, collapse = ", "))
  }
  if (!period_col %in% names(analysis_db)) stop("analysis_db 缺少周期列。")
  expected_prefix <- if (identical(period_col, "year")) "" else if (identical(period_col, "wave")) "Wave" else NULL
  if (is.null(expected_prefix)) stop("摘要周期列必须是 year 或 wave。")
  if (is.null(period_prefix)) period_prefix <- expected_prefix
  if (!identical(period_prefix, expected_prefix)) {
    expected_display <- if (nzchar(expected_prefix)) expected_prefix else "直接年份"
    stop("摘要周期术语与周期列不一致：", period_col, " 必须使用 ", expected_display, "。")
  }
  observed_periods <- sort(unique(as.integer(analysis_db[[period_col]])))
  if (is.null(expected_periods)) {
    expected_periods <- observed_periods
  } else {
    expected_periods <- sort(unique(as.integer(expected_periods)))
    unexpected_periods <- setdiff(observed_periods, expected_periods)
    if (length(unexpected_periods) > 0) {
      stop(
        "analysis_db 出现目标周期之外的记录：",
        paste(unexpected_periods, collapse = ", ")
      )
    }
  }

  variables <- as.character(analysis_codebook$Variable)
  if (anyNA(variables) || any(!nzchar(variables)) || anyDuplicated(variables)) {
    stop("analysis_codebook 的定义变量集合必须非空且不重复。")
  }
  if (!identical(names(meanings), variables) || any(!nzchar(meanings))) {
    stop("摘要含义必须按 analysis_codebook 的变量集合与顺序逐项人工填写。")
  }
  if (!identical(names(groups), variables) || any(!nzchar(groups))) {
    stop("摘要分组必须按 analysis_codebook 的变量集合与顺序逐项填写。")
  }
  if (!identical(names(meaning_reviewed), variables) ||
      anyNA(meaning_reviewed) || any(!meaning_reviewed)) {
    stop("摘要含义必须逐项完成人工核对：Criteria 定义与 codebook Label。")
  }
  if (any(!variables %in% names(analysis_db))) {
    stop("analysis_db 缺少 analysis_codebook 中的定义变量。")
  }
  if (any(is.na(analysis_codebook$Label) | !nzchar(trimws(analysis_codebook$Label)))) {
    stop("analysis_codebook Label 不能为空，摘要含义需与其核对。")
  }

  facts <- lapply(seq_along(variables), function(i) {
    variable <- variables[i]
    stats <- do.call(rbind, lapply(observed_periods, function(period) {
      idx <- analysis_db[[period_col]] == period
      total <- sum(idx, na.rm = TRUE)
      nonmissing <- sum(!is.na(analysis_db[[variable]][idx]))
      data.frame(period = period,
                 nonmissing = nonmissing,
                 total = total,
                 rate = if (total == 0) NA_real_ else nonmissing / total)
    }))
    covered <- stats[stats$nonmissing > 0 & !is.na(stats$rate), , drop = FALSE]
    object <- summary_object_text(covered, threshold, split_gap, period_prefix)

    if (all(covered$rate >= threshold) && !identical(object, "全样本")) {
      stop(variable, "：所有覆盖周期均达到阈值，但对象不是全样本。")
    }
    if (any(covered$rate < threshold) && identical(object, "全样本")) {
      stop(variable, "：存在低覆盖周期，但对象被写成全样本。")
    }
    if (grepl("有.*(题目信息|变量信息)|非缺失者", object)) {
      stop(variable, "：对象字段出现由结果反推对象的循环表达。")
    }

    raw_sources <- summary_split_sources(analysis_codebook$original_vars[i])
    if (!is.null(source_identity)) {
      if (is.null(names(source_identity))) stop("来源身份映射必须使用导出列名作为 names。")
      resolved_sources <- vapply(raw_sources, function(source) {
        if (source %in% names(source_identity)) return(unname(source_identity[source]))
        if (source %in% unname(source_identity)) return(source)
        NA_character_
      }, character(1))
      raw_sources <- unique(resolved_sources)
      if (anyNA(raw_sources) || any(!nzchar(raw_sources))) {
        stop(variable, "：mapping/original_vars 无法完整追溯到非空来源身份。")
      }
    }

    data.frame(
      group = unname(groups[i]),
      Variable = variable,
      meaning = unname(meanings[i]),
      raw_count = length(unique(raw_sources)),
      period = summary_period_text(
        covered$period,
        period_prefix,
        expected_periods
      ),
      object = object,
      coverage_period_count = nrow(covered),
      min_coverage = min(covered$rate),
      max_coverage = max(covered$rate),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, facts)
}

summary_markdown_rows <- function(facts) {
  paste0("| `", facts$Variable, "` | ", facts$meaning, " | ", facts$raw_count,
         " | ", facts$period, " | ", facts$object, " |")
}

validate_summary_markdown_rows <- function(rows, facts) {
  expected <- summary_markdown_rows(facts)
  if (!identical(rows, expected)) stop("摘要五列表渲染结果与事实表不一致。")
  invisible(TRUE)
}

summary_escape_html <- function(x) {
  x <- as.character(x)
  x <- gsub("&", "&amp;", x, fixed = TRUE)
  x <- gsub("<", "&lt;", x, fixed = TRUE)
  x <- gsub(">", "&gt;", x, fixed = TRUE)
  x <- gsub('"', "&quot;", x, fixed = TRUE)
  x
}

summary_render_inline_code <- function(x) {
  vapply(as.character(x), function(value) {
    positions <- gregexpr("`", value, fixed = TRUE)[[1]]
    if (length(positions) == 1L && positions[1] == -1L) {
      return(summary_escape_html(value))
    }
    if (length(positions) %% 2 != 0) stop("摘要文案中的反引号必须成对出现。")

    parts <- character()
    cursor <- 1L
    for (i in seq(1L, length(positions), by = 2L)) {
      open <- positions[i]
      close <- positions[i + 1L]
      if (open > cursor) {
        parts <- c(parts, summary_escape_html(substr(value, cursor, open - 1L)))
      }
      code_value <- substr(value, open + 1L, close - 1L)
      if (!nzchar(code_value)) stop("摘要文案中的 inline code 不能为空。")
      parts <- c(parts, paste0("<code>", summary_escape_html(code_value), "</code>"))
      cursor <- close + 1L
    }
    if (cursor <= nchar(value)) {
      parts <- c(parts, summary_escape_html(substr(value, cursor, nchar(value))))
    }
    paste0(parts, collapse = "")
  }, character(1), USE.NAMES = FALSE)
}

summary_validate_insight_inline_code <- function(items) {
  items <- as.character(items)
  if (any(grepl("</?code\\b|&lt;/?code\\b", items, ignore.case = TRUE, perl = TRUE))) {
    stop("小book提示中的变量名请使用成对反引号，不要手写 <code> 标签。")
  }

  unmarked <- unique(unlist(lapply(items, function(value) {
    plain <- gsub("`[^`]*`", "", value, perl = TRUE)
    hits <- regmatches(
      plain,
      gregexpr(
        "(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*[0-9][A-Za-z0-9_]*)(?![A-Za-z0-9_])",
        plain,
        perl = TRUE
      )
    )[[1]]
    hits[nzchar(hits)]
  }), use.names = FALSE))

  if (length(unmarked) > 0) {
    stop(
      "小book提示中的变量名必须使用成对反引号：",
      paste(unmarked, collapse = "、")
    )
  }
  invisible(TRUE)
}

summary_count_span <- function(value,
                               suffix,
                               theme_color,
                               weight = 400,
                               role = NULL) {
  role_attr <- if (is.null(role)) "" else paste0(' data-summary-count-role="', role, '"')
  paste0(
    '<span data-summary-measure="true" style="white-space:nowrap;">',
    '<span data-summary-count="true"', role_attr,
    ' style="color:', theme_color, ';font-weight:', weight, ';">',
    summary_escape_html(value), '</span>', summary_escape_html(suffix), '</span>'
  )
}

summary_path_span <- function(path, theme_color) {
  paste0(
    '<span data-summary-path="true" style="color:', theme_color,
    ';font-style:italic;">', summary_escape_html(path), '</span>'
  )
}

summary_concept_span <- function(concept, theme_color) {
  paste0(
    '“<span data-summary-concept="true" style="color:', theme_color,
    ';font-weight:400;">', summary_escape_html(concept), '</span>”'
  )
}

summary_path_part <- function(path) {
  list(type = "path", value = as.character(path))
}

summary_count_part <- function(value,
                               suffix,
                               weight = 400,
                               role = NULL) {
  list(
    type = "count",
    value = value,
    suffix = as.character(suffix),
    weight = weight,
    role = role
  )
}

summary_concept_part <- function(concept) {
  list(type = "concept", value = as.character(concept))
}

summary_render_parts <- function(parts, theme_color) {
  if (!is.list(parts) || length(parts) == 0) stop("摘要语义片段不能为空。")
  rendered <- vapply(parts, function(part) {
    if (is.character(part) && length(part) == 1) {
      return(summary_render_inline_code(part))
    }
    if (!is.list(part) || is.null(part$type) || is.null(part$value)) {
      stop("摘要语义片段必须是文本或带 type/value 的结构。")
    }
    if (identical(part$type, "path")) {
      return(summary_path_span(part$value, theme_color))
    }
    if (identical(part$type, "count")) {
      suffix <- if (is.null(part$suffix)) "" else part$suffix
      weight <- if (is.null(part$weight)) 400 else part$weight
      role <- if (is.null(part$role)) NULL else part$role
      return(summary_count_span(part$value, suffix, theme_color, weight, role))
    }
    if (identical(part$type, "concept")) {
      return(summary_concept_span(part$value, theme_color))
    }
    stop("未知的摘要语义片段类型：", part$type)
  }, character(1))
  paste0(rendered, collapse = "")
}

summary_join_concepts <- function(concepts, final_count, theme_color) {
  concepts <- as.character(concepts)
  if (length(concepts) == 0 || any(!nzchar(concepts))) stop("摘要定义概念不能为空。")
  if (final_count < length(concepts)) stop("展示的定义概念数不能超过最终变量数。")
  rendered <- vapply(concepts, summary_concept_span, character(1), theme_color = theme_color)
  if (final_count > length(rendered)) return(paste0(paste0(rendered, collapse = ""), "等 "))
  if (length(rendered) == 1) return(rendered)
  paste0(paste0(rendered[-length(rendered)], collapse = ""), "和", rendered[length(rendered)])
}

render_summary_entry_paragraph <- function(entry, theme_color) {
  if (!is.null(entry$parts)) {
    return(summary_render_parts(entry$parts, theme_color))
  }
  entry_type <- if (is.null(entry$type)) "directory" else entry$type
  description <- if (is.null(entry$description)) "" else entry$description
  if (!nzchar(description)) stop("摘要第一段的主题内容说明不能为空。")

  if (identical(entry_type, "directory")) {
    paths <- as.character(entry$paths)
    if (length(paths) == 0 || any(!nzchar(paths))) stop("目录入口不能为空。")
    path_text <- paste(
      vapply(paths, summary_path_span, character(1), theme_color = theme_color),
      collapse = "、"
    )
    prefix <- paste0("从 dbCodeBook 的目录 ", path_text, " 进入，可以看到 ")
  } else if (identical(entry_type, "search")) {
    keyword <- as.character(entry$keyword)
    if (length(keyword) != 1 || !nzchar(keyword)) stop("普通检索关键词不能为空。")
    prefix <- paste0("在 dbCodeBook 中，通过 ", summary_escape_html(keyword), " 检索，可以看到 ")
  } else {
    stop("摘要入口类型只能是 directory 或 search。")
  }

  count_text <- ""
  if (!is.null(entry$count)) {
    count_text <- summary_count_span(entry$count, " 条", theme_color, weight = 400)
  }
  paste0(prefix, count_text, summary_render_inline_code(description))
}

render_summary_selection_paragraph <- function(selection, theme_color) {
  if (!is.null(selection$parts)) {
    return(summary_render_parts(selection$parts, theme_color))
  }
  required <- c("raw_count", "concepts", "final_count")
  missing <- required[!vapply(required, function(name) !is.null(selection[[name]]), logical(1))]
  if (length(missing) > 0) stop("摘要第二段缺少字段：", paste(missing, collapse = ", "))
  relation <- if (is.null(selection$relation)) "" else selection$relation
  relation_prefix <- if (is.null(selection$relation_prefix)) "，" else selection$relation_prefix
  relation_text <- if (nzchar(relation)) {
    paste0(relation_prefix, summary_render_inline_code(relation))
  } else {
    ""
  }
  before_count <- if (is.null(selection$before_count)) "" else selection$before_count
  paste0(
    "本次从中选取 ",
    summary_count_span(selection$raw_count, " 个", theme_color, weight = 400),
    "原始变量，定义",
    summary_join_concepts(selection$concepts, selection$final_count, theme_color),
    before_count,
    summary_count_span(
      selection$final_count,
      " 个变量",
      theme_color,
      weight = 500,
      role = "definition"
    ),
    relation_text
  )
}

render_summary_insight_card <- function(items,
                                        theme_color,
                                        variant = c("standard", "compact")) {
  variant <- match.arg(variant)
  items <- as.character(items)
  if (length(items) == 0 || any(!nzchar(items))) stop("小book提示文案不能为空。")
  summary_validate_insight_inline_code(items)
  body <- paste(summary_render_inline_code(items), collapse = "<br>")
  if (identical(variant, "compact")) {
    return(c(
      "<!-- summary-insight-card:start -->",
      '<div class="summary-insight-card" data-summary-insight-card="true" style="background:#F4F3F0;border:1px solid #F4F3F0;border-radius:10px;padding:14px 16px;">',
      paste0(
        '<div class="summary-insight-title" data-summary-insight-title="true" ',
        'style="color:', theme_color,
        ';font-weight:700;margin-bottom:6px;">小book提示</div>'
      ),
      paste0(
        '<div class="summary-insight-body" data-summary-insight-body="true">',
        body, '</div>'
      ),
      "</div>",
      "<!-- summary-insight-card:end -->"
    ))
  }
  c(
    "<!-- summary-insight-card:start -->",
    '<div class="summary-insight-card" data-summary-insight-card="true" style="box-sizing:border-box;margin:18px 0;padding:20px 24px 22px;background:#F4F3F0;border:1px solid #F4F3F0;border-radius:10px;box-shadow:none;">',
    paste0(
      '<div class="summary-insight-title" data-summary-insight-title="true" ',
      'style="margin:0 0 12px;font-size:18px;line-height:1.5;font-weight:700;color:',
      theme_color, ';">小book提示</div>'
    ),
    paste0(
      '<div class="summary-insight-body" data-summary-insight-body="true" ',
      'style="font-size:16px;line-height:1.85;font-style:normal;font-weight:400;',
      'color:#344054;letter-spacing:0;">', body, '</div>'
    ),
    "</div>",
    "<!-- summary-insight-card:end -->"
  )
}

render_summary_note_section <- function(entry,
                                        selection,
                                        summary_rows,
                                        theme_color,
                                        insight_items = NULL,
                                        insight_variant = c("standard", "compact")) {
  insight_variant <- match.arg(insight_variant)
  if (length(summary_rows) == 0 || any(!nzchar(summary_rows))) {
    stop("摘要五列表不能为空。")
  }
  lines <- c(
    "## 摘要导读",
    "",
    render_summary_entry_paragraph(entry, theme_color),
    "",
    render_summary_selection_paragraph(selection, theme_color),
    "",
    "| 定义变量 | 含义 | 组成 | 覆盖周期 | 对象 |",
    "| --- | --- | ---: | --- | --- |",
    summary_rows,
    "",
    "<br>"
  )
  summary_table_range <- c(
    start = 7L,
    end = 8L + length(summary_rows)
  )
  if (!is.null(insight_items)) {
    lines <- c(lines, render_summary_insight_card(
      insight_items,
      theme_color,
      variant = insight_variant
    ))
  }
  result <- c(lines, "")
  attr(result, "summary_table_range") <- summary_table_range
  result
}
