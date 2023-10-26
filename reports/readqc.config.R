report_title <- "RNA-seq analysis of IFT88 knock-down timecourse"
report_author <- "Stephen Sansom"

# location of the readqc_db
readqc_db="/gfs/work/ssansom/angus_ift88/readqc/csvdb"

# location of the scseq_db
name_field_titles=c("knockdown","timepoint","replicate")
qc_name_field_titles=c(name_field_titles, "lane")
plot_groups = c("knockdown","timepoint")
experiment_groups = c("knockdown","timepoint")
plot_color="timepoint"
plot_shape="knockdown"
plot_label="replicate"
nreplicates=3

# exclude samples from analysis.
exclude <- c()