#' A helper function to retrieve Fastqc results from the pipeline_readqc database
#' 
#' @export
#' 
fetchFastQC <- function(qc_metric, 
                        db = fastqc_sqlite_database)

{
    require(RSQLite)
    require(DBI)
    
    con <- dbConnect(RSQLite::SQLite(), dbname = db)
    tables <- dbListTables(con)

    table_name <- paste("fastqc",qc_metric,sep="_")

    if(!table_name %in% tables)
    {
        print(paste0("Table: ",table_name," not found in ",db))
        print("Avaliable tables are:")
        print(tables)
        return(NULL)
    }
    
    statement = paste0("select * from fastqc_", qc_metric," qc",
                       " left join fastqs f",
                       " on qc.sample_id=f.seq_id",
                       " left join samples s",
                       " on f.sample_id = s.sample_id")
    
    result <- dbSendQuery(con,statement)
    data <- dbFetch(result)
    dbDisconnect(con)
    
    #print(head(data))
    
    # get rid of duplicated sample_id columns
    data <- data[,!duplicated(colnames(data))]
    
    colnames(data) <- gsub(" ","_", colnames(data))
    colnames(data) <- gsub("-","_", colnames(data))
    
    # Fix issue with encode of base position.
    # sometimes base position is encoded as a character variable that includes ranges, 
    # e.g. c("1-10","11","12","13-20",....)
    # to fix this, we replace the range with the start position of the range,
    # and convert the "Base" variable to numeric
    # i.e. so the above becomes c(1,11,12,13)
    
    if("Base" %in% colnames(data)) {
    data$Base <- gsub("([^-]+).*","\\1",data$Base)
    data$Base <- as.numeric(data$Base) }
    
    
    
    data
}

