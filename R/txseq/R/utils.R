#' Copy the report template to the current working directory
#' @param report The report template to fetch ("readqc" or "rnaseq")
#' 
#' @export
#'   
getReport <- function(report="readqc")
{
  report_path <- file.path(system.file(package="ngsfoo"),
                           "reports",report)
  files <- list.files(report_path, full.names=TRUE)
  file.copy(files,
            ".")
}


#' Copy the report template to the current working directory
#' 
#' @export
#'   
showReports <- function()
{
  report_path <- file.path(system.file(package="ngsfoo"),
                           "reports")
  files <- list.files(report_path)
  files
}


#' Copy the report template to the current working directory
#' @param topic The topic of the examples to fetch
#' 
#' @export
#'   
getExamples <- function(topic="clustering")
{
  report_path <- file.path(system.file(package="ngsfoo"),
                           "examples", topic)
  files <- list.files(report_path, full.names=TRUE)
  file.copy(files,
            ".")
}


#' Copy the report template to the current working directory
#' 
#' @export
#'   
showExamples <- function()
{
  report_path <- file.path(system.file(package="ngsfoo"),
                           "examples")
  files <- list.files(report_path)
  files
}


