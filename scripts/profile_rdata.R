#!/usr/bin/env Rscript
# Profile the contents of .RData / .RDS deposits before anything is built from
# them. The question every deposit has to answer first is whether it holds real
# fixes -- coordinates AND a timestamp, for predators as well as prey -- or only
# the analysis tables that were derived from them.
#
# Usage:  Rscript scripts/profile_rdata.R data/raw/kh1893292/*.RData

suppressWarnings(suppressMessages({
  options(stringsAsFactors = FALSE, width = 200)
}))

COORD <- "^(x|y|lon|long|longitude|lat|latitude|utm[._]?[xy]|easting|northing|mu\\.[xy]|coords?\\.[xy][0-9]?)$"
TIME  <- "(time|date|timestamp|datetime|fixtime|acquisition|dt)"
IDCOL <- "^(id|animal|animalid|animal_id|indiv|individual|collar|collarid|collar_id|uniqueid|tag)"
SPP   <- "(species|spp|taxa|taxon)"

fmt_num <- function(x) formatC(x, format = "d", big.mark = ",")

matching <- function(cols, pattern) cols[grepl(pattern, tolower(cols))]

# The interesting number is not the mean gap but the one the collar was
# programmed to, so report the median and how tightly the gaps cluster on it.
fix_interval <- function(times, ids) {
  gaps <- unlist(lapply(split(times, ids), function(t) {
    t <- sort(t[!is.na(t)])
    if (length(t) < 2) return(numeric(0))
    as.numeric(diff(t), units = "hours")
  }), use.names = FALSE)
  gaps <- gaps[is.finite(gaps) & gaps > 0]
  if (!length(gaps)) return("  fix interval: not derivable")
  med <- stats::median(gaps)
  on_schedule <- mean(abs(gaps - med) < 0.1 * med) * 100
  sprintf("  fix interval: median %.2f h  (%.0f%% of %s gaps within 10%% of it; q05=%.2f q95=%.2f)",
          med, on_schedule, fmt_num(length(gaps)), stats::quantile(gaps, 0.05), stats::quantile(gaps, 0.95))
}

as_time <- function(v) {
  if (inherits(v, c("POSIXct", "POSIXt", "Date"))) return(as.POSIXct(v, tz = "UTC"))
  if (is.character(v) || is.factor(v)) {
    t <- suppressWarnings(as.POSIXct(as.character(v), tz = "UTC"))
    if (sum(!is.na(t)) > 0.5 * length(t)) return(t)
  }
  NULL
}

describe_frame <- function(df, label) {
  df <- as.data.frame(df)
  cols <- names(df)
  cat(sprintf("\n  %s -- data frame, %s rows x %d cols\n", label, fmt_num(nrow(df)), ncol(df)))
  cat("  columns:\n")
  for (cn in cols) {
    v <- df[[cn]]
    ex <- if (all(is.na(v))) "NA" else paste(utils::head(format(v[!is.na(v)]), 2), collapse = " | ")
    cat(sprintf("    %-28s %-14s nuniq=%-9s nNA=%-9s ex= %s\n",
                substr(cn, 1, 28), paste(class(v), collapse = "/"),
                fmt_num(length(unique(v))), fmt_num(sum(is.na(v))), substr(ex, 1, 46)))
  }

  coord_cols <- matching(cols, COORD)
  time_cols  <- matching(cols, TIME)
  id_cols    <- matching(cols, IDCOL)
  spp_cols   <- matching(cols, SPP)
  cat(sprintf("\n  VERDICT INPUTS  coords=[%s]  time=[%s]  id=[%s]  species=[%s]\n",
              paste(coord_cols, collapse = ","), paste(time_cols, collapse = ","),
              paste(id_cols, collapse = ","), paste(spp_cols, collapse = ",")))

  for (cn in coord_cols) {
    v <- suppressWarnings(as.numeric(df[[cn]]))
    if (any(is.finite(v))) cat(sprintf("  range %-12s %.3f .. %.3f\n", cn, min(v, na.rm = TRUE), max(v, na.rm = TRUE)))
  }

  tcol <- NULL
  for (cn in time_cols) {
    t <- as_time(df[[cn]])
    if (!is.null(t) && any(!is.na(t))) {
      cat(sprintf("  span  %-12s %s .. %s\n", cn, min(t, na.rm = TRUE), max(t, na.rm = TRUE)))
      if (is.null(tcol)) tcol <- t
    }
  }

  idv <- if (length(id_cols)) df[[id_cols[1]]] else NULL
  if (!is.null(idv)) cat(sprintf("  individuals:  %s distinct %s\n", fmt_num(length(unique(idv))), id_cols[1]))
  if (length(spp_cols)) {
    tab <- table(df[[spp_cols[1]]], useNA = "ifany")
    cat("  by species:\n")
    for (nm in names(tab)) {
      n_ind <- if (!is.null(idv)) length(unique(idv[df[[spp_cols[1]]] == nm])) else NA
      cat(sprintf("    %-24s %10s rows  %s individuals\n", nm, fmt_num(tab[[nm]]),
                  if (is.na(n_ind)) "?" else fmt_num(n_ind)))
    }
  }
  if (!is.null(tcol) && !is.null(idv)) cat(fix_interval(tcol, idv), "\n")
}

describe <- function(obj, label, depth = 0) {
  if (depth > 3) return(invisible(NULL))
  if (is.data.frame(obj)) return(describe_frame(obj, label))
  cls <- paste(class(obj), collapse = "/")
  if (is.list(obj)) {
    nms <- names(obj)
    if (is.null(nms)) nms <- paste0("[[", seq_along(obj), "]]")
    cat(sprintf("\n  %s -- %s, %d element(s): %s\n", label, cls,
                length(obj), paste(utils::head(nms, 30), collapse = ", ")))
    # A crawl/HMM fit is a list of per-animal frames; the frames are the point.
    for (i in seq_along(obj)) {
      el <- obj[[i]]
      if (is.data.frame(el) || is.list(el)) describe(el, paste0(label, "$", nms[i]), depth + 1)
    }
    return(invisible(NULL))
  }
  cat(sprintf("\n  %s -- %s, length %s\n", label, cls, fmt_num(length(obj))))
}

for (path in commandArgs(trailingOnly = TRUE)) {
  cat(strrep("=", 100), "\n")
  cat("FILE ", path, sprintf("  (%.1f MB)\n", file.size(path) / 1e6))
  if (grepl("\\.rds$", path, ignore.case = TRUE)) {
    describe(readRDS(path), basename(path))
  } else {
    e <- new.env()
    nms <- load(path, envir = e)
    cat("objects: ", paste(nms, collapse = ", "), "\n")
    for (nm in nms) describe(get(nm, envir = e), nm)
    rm(e)
  }
  gc(verbose = FALSE)
}
