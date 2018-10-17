## Extract transcript information from a GTF file

message("tabulate_transcript_information.R")
timestamp()

# Libraries ----

stopifnot(
    require(optparse),
    require(rtracklayer)
)

# Test data ----

opt <- list(
    gtf = "annotations.dir/quantitation.geneset.gtf.gz",
    fields = 'gene_id,transcript_id,gene_biotype,transcript_biotype,gene_name',
    outfile = "output.txt.gz"
)

# Options ----

option_list <- list(
    make_option(
    	c("--gtf"),
    	help="Path to GTF file to extract transcripts information from."),
    make_option(
    	c("--fields"), default = "",
    	help="Comma-separated list of fields to extract from the GTF metadata."),
    make_option(
    	c("--outfile"),
    	help="outfile")
    )

opt <- parse_args(OptionParser(option_list=option_list))

cat("Running with options:\n")
print(opt)

# Import data from GTF file ----

stopifnot(file.exists(opt$gtf))
gtfData <- import.gff(opt$gtf, feature.type="transcript")
cat("Transcripts parsed from GTF:\n")
length(gtfData)

# Extract fields of interest ----

fieldsExtract <- strsplit(opt$fields, ",")[[1]]

if (!all(fieldsExtract %in% colnames(mcols(gtfData)))) {
    stop("fields arguments contains invalid field names")
}

fieldsData <- mcols(gtfData)[, fieldsExtract]
cat("Dimensions of extracted transcript table:\n")
dim(fieldsData)

fieldsData <- unique(fieldsData)
cat("Dimensions of deduplicated transcript table:\n")
dim(fieldsData)

# Store the pointer to the connection, to close it cleanly later
outgz <- gzfile(opt$outfile, "wt")

cat("Writing transcript table to:", opt$outfile, " ... ")
write.table(fieldsData, outgz,
            quote=FALSE, col.names=TRUE,
            row.names=FALSE, sep="\t")
close(outgz)
cat("Done.\n")

timestamp()
message("Completed")