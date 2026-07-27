compose_definition_note_lines <- function(
    summary_section,
    definition_html_lines,
    reference_lines,
    extract_box,
    publish_code,
    detail_html_lines) {
  c(
    summary_section,
    "## 定义", "", definition_html_lines, "",
    if (length(reference_lines) > 0) c(reference_lines, "") else character(),
    "## 材料", "", "### 1-提取变量", "", extract_box, "",
    "### 2-代码材料", "", paste0(strrep(intToUtf8(96), 3), "r"),
    publish_code, paste0(strrep(intToUtf8(96), 3)), "",
    detail_html_lines
  )
}

render_definition_bundle <- function(
    data,
    db_data,
    codebook,
    analysis_data,
    analysis_codebook,
    analysis_vars,
    raw_vars,
    raw_codebook,
    criteria,
    summary_meanings,
    summary_groups,
    summary_entry,
    summary_selection,
    summary_insight_items,
    file_stem,
    note_name,
    qa_title,
    transaction_id,
    script_file,
    theme_color = "#A33842",
    cycle_order = c("2011", "2013", "2015", "2018", "2020"),
    raw_source_years = NULL,
    raw_row_count = nrow(data),
    hist_binwidth = 1,
    hist_mode = "linear",
    evidence_lines = character(),
    reference_lines = character()) {
  for (pkg in c("dplyr", "tidyr", "dbCodeBookr")) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      stop("Required package is not installed: ", pkg)
    }
  }
  library("dplyr")
  library("tidyr")
  library("dbCodeBookr")
  expected_charls_cycles <- c("2011", "2013", "2015", "2018", "2020")
  if (!identical(as.character(cycle_order), expected_charls_cycles)) {
    stop(
      "CHARLS target cycles must be 2011, 2013, 2015, 2018, and 2020; ",
      "a topic cannot redefine full-cycle coverage from its observed rows."
    )
  }
  stopifnot(identical(analysis_vars, analysis_codebook$Variable))
  stopifnot(all(analysis_vars %in% names(criteria)))
  stopifnot(all(nzchar(criteria[analysis_vars])))

  format_n <- function(x) {
    format(x, big.mark = ",", scientific = FALSE)
  }

  summary_reviewed <- setNames(rep(TRUE, length(analysis_vars)), analysis_vars)
  summary_facts <- build_summary_facts(
    analysis_data,
    analysis_codebook,
    summary_meanings,
    summary_groups,
    summary_reviewed,
    period_col = "year",
    expected_periods = cycle_order
  )
  summary_rows <- summary_markdown_rows(summary_facts)
  validate_summary_markdown_rows(summary_rows, summary_facts)

  coverage <- analysis_data %>%
    select(year, all_of(analysis_vars)) %>%
    pivot_longer(
      cols = all_of(analysis_vars),
      names_to = "Variable",
      values_to = "Value"
    ) %>%
    group_by(year, Variable) %>%
    summarise(
      nonmissing = sum(!is.na(Value)),
      missing = sum(is.na(Value)),
      .groups = "drop"
    ) %>%
    arrange(year, match(Variable, analysis_vars))

  qa_lines <- c(
    qa_title,
    "",
    "1. raw / recover",
    paste0("- recover transaction: ", transaction_id),
    paste0("- raw rows: ", format_n(raw_row_count)),
    paste0("- analysis rows: ", format_n(nrow(analysis_data))),
    paste0("- raw variables: ", format_n(length(raw_vars))),
    "",
    "2. final variables",
    paste0("- ", paste(analysis_vars, collapse = ", ")),
    "",
    "3. yearly coverage",
    capture.output(print(coverage)),
    "",
    "4. summary facts",
    capture.output(print(summary_facts)),
    "",
    "5. evidence boundary",
    paste0("- ", evidence_lines)
  )
  writeLines(
    qa_lines,
    paste0("CHARLS_", file_stem, "_QA.txt"),
    useBytes = TRUE
  )

  detail_data <- db_data
  if (!is.null(raw_source_years)) {
    for (var_name in intersect(names(raw_source_years), names(detail_data))) {
      active <- as.character(detail_data$year) %in%
        as.character(raw_source_years[[var_name]])
      detail_data[[var_name]][!active] <- NA
    }
  }

  details <- generate_var_details(
    detail_data,
    bar_color = paste0(theme_color, "90"),
    show_hist = TRUE,
    hist_binwidth = hist_binwidth,
    hist_mode = hist_mode,
    show_distribution_nav = FALSE,
    show_cycle_heatmap = FALSE
  )
  names(details) <- names(db_data)
  codebook$detail <- unname(details[codebook$Variable])
  codebook$easylabel <- codebook$Label

  z <- detail_data[, setdiff(names(detail_data), c("ID", "id"))]
  counts <- sapply(setdiff(names(z), "year"), function(col) {
    tapply(z[[col]], z$year, function(x) sum(!is.na(x)))
  })
  count_data <- as.data.frame(counts) %>%
    mutate(year = rownames(.)) %>%
    pivot_longer(
      cols = -year,
      names_to = "Variable",
      values_to = "Count"
    )
  wide_data <- pivot_wider(
    count_data,
    names_from = year,
    values_from = Count,
    values_fill = NA,
    names_sort = FALSE
  )
  wide_data <- wide_data[
    order(factor(wide_data$Variable, levels = names(db_data))),
  ]
  wide_data$category <- ifelse(
    wide_data$Variable %in% analysis_vars,
    "Defined variables",
    "Source variables"
  )
  wide_data$category <- factor(
    wide_data$category,
    levels = c("Source variables", "Defined variables")
  )
  wide_data <- wide_data[
    order(wide_data$category, match(wide_data$Variable, names(db_data))),
  ]

  heat_df <- left_join(
    wide_data,
    codebook[, c("Variable", "original_vars", "easylabel")],
    by = "Variable"
  )
  meta_df <- left_join(wide_data, codebook, by = "Variable")
  generate_html_definition_long(
    heat_df,
    meta_df,
    paste0("CHARLS_", file_stem, "_detail.html"),
    "#2c3e50",
    theme_color
  )

  definition_data <- meta_df[
    meta_df$Variable %in% analysis_vars,
    c("Variable", "original_vars", "detail")
  ]
  definition_data <- definition_data[
    match(analysis_vars, definition_data$Variable),
  ]
  definition_details <- generate_var_details(
    detail_data,
    bar_color = paste0(theme_color, "90"),
    show_hist = TRUE,
    hist_binwidth = hist_binwidth,
    hist_mode = hist_mode,
    show_distribution_nav = TRUE,
    show_cycle_heatmap = TRUE,
    cycle_col = "year",
    cycle_order = cycle_order,
    heatmap_color = theme_color
  )
  names(definition_details) <- names(db_data)
  definition_data$detail <- unname(
    definition_details[definition_data$Variable]
  )
  definition_data$Definition <- definition_data$Variable
  definition_data$Criteria <- unname(criteria[definition_data$Variable])
  definition_data <- definition_data[
    c("Variable", "original_vars", "Definition", "Criteria", "detail")
  ]
  generate_html_definition(
    definition_data,
    paste0("CHARLS_", file_stem, "_definition.html"),
    theme_color
  )

  clean_html <- function(path) {
    text <- readLines(path, encoding = "UTF-8", warn = FALSE)
    text <- gsub("mapping", "varlink", text, fixed = TRUE)
    text <- gsub("&emsp;&emsp;", "", text, fixed = TRUE)
    writeLines(text, path, useBytes = TRUE)
  }
  clean_html(paste0("CHARLS_", file_stem, "_detail.html"))
  clean_html(paste0("CHARLS_", file_stem, "_definition.html"))

  extract_vars <- paste0(raw_codebook$Variable, "=", raw_codebook$newname)
  extract_box <- c(
    '<div class="custom-textbox">',
    '<div class="textbox-content">',
    paste0(extract_vars, collapse = ",\n"),
    "</div>",
    paste0(
      '<button class="textbox-button" ',
      'onclick="goToExtractVariables(this)">Go to 提取变量</button>'
    ),
    "</div>"
  )

  script_lines <- readLines(
    script_file,
    encoding = "UTF-8",
    warn = FALSE
  )
  output_idx <- grep("^# 输出$", script_lines)
  publish_code <- if (length(output_idx) == 0) {
    script_lines
  } else {
    script_lines[seq_len(output_idx[1] - 1)]
  }
  definition_html_lines <- readLines(
    paste0("CHARLS_", file_stem, "_definition.html"),
    encoding = "UTF-8",
    warn = FALSE
  )
  detail_html_lines <- readLines(
    paste0("CHARLS_", file_stem, "_detail.html"),
    encoding = "UTF-8",
    warn = FALSE
  )

  summary_section <- render_summary_note_section(
    entry = summary_entry,
    selection = summary_selection,
    summary_rows = summary_rows,
    theme_color = theme_color,
    insight_items = summary_insight_items,
    insight_variant = "compact"
  )
  note_lines <- compose_definition_note_lines(
    summary_section,
    definition_html_lines,
    reference_lines,
    extract_box,
    publish_code,
    detail_html_lines
  )
  writeLines(note_lines, note_name, useBytes = TRUE)
}
