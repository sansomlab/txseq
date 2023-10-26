#' Helper function for setting a group on a data frame
#' @export
setGroup <- function(dataFrame, groupName, members)
{
  if(length(members) > 1)
  {
    dataFrame[[groupName]] <- do.call(paste, c(dataFrame[,members], sep="_"))
  } else {
    dataFrame[[groupName]] <- dataFrame[[members[1]]]
  }
  dataFrame
}