#' Wrapper function for reading data
#' from an SQLite databases
#' @param sql_query An sql query statement
#' @param database  Location of an sqlite database
#' 
#' @import RSQLite
#'
#' @export
#' 
fetch_DataFrame <- function(sql_query, 
                            database,
                            attach=NULL)
  {
        drv <- dbDriver("SQLite")
        con <- dbConnect(drv,dbname=database)
        
        if(!is.null(attach))
        {
          dbExecute(con, attach) 
        }
        
        df <- dbGetQuery(con, sql_query)
        
        dbDisconnect(con)
        return(df)
  }

#' Wrapper function for writing data
#' to an SQLite database
#' @param sql_query An sql query statement
#' @param database  Location of an sqlite database
#'
#' @import RSQLite
#'
#' @export
#' 
write_DataFrame <- function(TableName,
		            DataFrame,
			    database,
			    overwrite=FALSE,
			    rownames=FALSE)
  {
        drv <- dbDriver("SQLite")
        con <-dbConnect(drv,dbname=database)
        dbWriteTable(con, TableName, DataFrame, overwrite=overwrite, row.names=rownames)
        dbDisconnect(con)
  }
