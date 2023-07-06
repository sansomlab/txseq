report_title <- "RNA-seq analysis of IFT88 knock-down timecourse"
report_author <- "Stephen Sansom"

# location of the readqc_db
readqc_db="/gfs/work/ssansom/angus_ift88/readqc/csvdb"

# location of the scseq_db
scseq_db="/gfs/work/ssansom/angus_ift88/scseq_good/csvdb"
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

# DESeq2 parameters
location_function <- "median"
fit_type <- "local"
experimental_design <- "~experiment_group"
reference_levels <- list(knockdown = "control", timepoint = "0hr")
contrasts <- list("control_0hr_vs_IFT88_0hr"=c("experiment_group","control_0hr", "IFT88_0hr"),
                  "control_1hr_vs_IFT88_1hr"=c("experiment_group","control_1hr", "IFT88_1hr"),
                  "control_2hr_vs_IFT88_2hr"=c("experiment_group","control_2hr", "IFT88_2hr"),
                  "control_4hr_vs_IFT88_4hr"=c("experiment_group","control_4hr", "IFT88_4hr"),
                  "control_8hr_vs_IFT88_8hr"=c("experiment_group","control_8hr", "IFT88_8hr"),
                  "control_24hr_vs_IFT88_24hr"=c("experiment_group","control_24hr", "IFT88_24hr"))

p_value_threshold <- 0.05
abs_fc_threshold <- 1.5
n_interesting_genes <- 15
hm_row_cex <- 0.8
hm_col_cex <- 0.8