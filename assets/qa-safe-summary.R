# QA coverage helpers for mixed-type analysis variables.
#
# Use this template when the analysis variables include both numeric binary
# variables and character/factor category variables. The helper converts only
# the QA summary copy to character before pivot_longer(); it does not modify the
# source analysis data or the formal output variable types.

library("dplyr")
library("tidyr")

safe_coverage_long <- function(data, vars, year_var = "year") {
  missing_vars <- setdiff(c(year_var, vars), names(data))
  if (length(missing_vars) > 0) {
    stop(
      "safe_coverage_long() missing columns: ",
      paste(missing_vars, collapse = ", "),
      call. = FALSE
    )
  }

  data %>%
    dplyr::select(dplyr::all_of(c(year_var, vars))) %>%
    dplyr::mutate(
      dplyr::across(dplyr::all_of(vars), ~ dplyr::if_else(is.na(.x), NA_character_, as.character(.x)))
    ) %>%
    tidyr::pivot_longer(
      cols = dplyr::all_of(vars),
      names_to = "variable",
      values_to = "value"
    ) %>%
    dplyr::group_by(.data[[year_var]], .data$variable) %>%
    dplyr::summarise(
      non_missing_n = sum(!is.na(.data$value)),
      missing_n = sum(is.na(.data$value)),
      .groups = "drop"
    ) %>%
    dplyr::arrange(.data[[year_var]], .data$variable)
}

# Minimal example -----------------------------------------------------------
# `binary_numeric` is numeric 1/0, while `category_text` is character. The
# original types are preserved in `example_data`; only the QA summary copy is
# temporarily converted before long-format aggregation.

example_data <- tibble::tibble(
  year = c(2011, 2011, 2013, 2013),
  binary_numeric = c(1, 0, NA, 1),
  category_text = c("Still Smoke", "Quit", NA, "Never Smoked")
)

example_summary <- safe_coverage_long(
  example_data,
  vars = c("binary_numeric", "category_text")
)

stopifnot(is.numeric(example_data$binary_numeric))
stopifnot(is.character(example_data$category_text))
print(example_summary)
