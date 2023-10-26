#' A helper function to retrieve Fastqc results from the pipeline_readqc database
#' 
#' @export
#' 
fetchReadqcLegacy <- function(qc_metric, db=readqc_db,
                        name_fields=qc_name_field_titles,
                        plot_group_names=plot_groups,
                        paired=TRUE)
{
    tracks = fetch_DataFrame("select distinct filename from status_summary",db)
    tracks$sample = basename(tracks$filename)

    # drop samples starting with "trimmed".
    tracks <- tracks[!grepl("trimmed",tracks$sample),]
    rownames(tracks) <- tracks$sample

    begin <- TRUE
    
    # drop samples returning no data
    for(sample in tracks$sample)
    {
        sample <- gsub("\\.","_",sample)

        stat <- paste0("select * from ", sample, "_", qc_metric)
        temp <- fetch_DataFrame(stat, db)

        if(nrow(temp) == 0)
        {
            message("Warning: no data retrieved for", sample)
        } else {
            temp$sample <- sample
            if(begin==TRUE)
            {
                results <- temp
                begin <- FALSE
            } else {
                results <- rbind(results,temp)
            }
        }
    }

    sample_info <- read.table(text=results$sample,header=F,sep="_",as.is=T)

    if(paired)
    {
        default_cols <- c("fastq","end","fastqc")
    } else {
        default_cols <- c("fastq","fastqc")
    }

    colnames(sample_info) <- c(name_fields, default_cols)
    results <- data.frame(cbind(results,sample_info))

    results <- setGroup(results,"plot_group", plot_group_names)
    
    results
}


#' A helper function to retrieve Fastqc results from the pipeline_readqc database
#' 
#' @export
#' 
fetchReadqc <- function(qc_metric, db=readqc_db,
                              name_fields=qc_name_field_titles,
                              plot_group_names=plot_groups,
                              paired=TRUE)
{
  
  statement = paste0("select * from fastqc_",qc_metric)
  
  # get the results
  data = fetch_DataFrame(statement, db)
  
  # add the name field columns
  data$sample <- gsub("-","_",data$track)
  if(paired) { name_fields <- c(name_fields, "end") }
  
  field_cols <- read.table(text=data$sample, sep="_")
  colnames(field_cols) <- name_fields
  
  results <- cbind(data, field_cols)
  
  results <- setGroup(results,"plot_group", plot_group_names)
  
  # santise the results column names
  colnames(results) <- gsub(" ", "_", colnames(results))
  colnames(results) <- gsub("-", "_", colnames(results))
  colnames(results) <- gsub("/", "_", colnames(results))
  
  results
}



