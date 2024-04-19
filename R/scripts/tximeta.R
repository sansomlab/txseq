## Run tximeta

library(optparse)
suppressPackageStartupMessages(library(tximeta))
suppressPackageStartupMessages(library(tximport))

## deal with the options
option_list <- list(
    make_option(c("--indexdir"), default=NULL,
                help="the path to the Salmon index directory"),
    make_option(c("--salmondir"), default=NULL,
                help="the path to the per Salmon output folders"),
    make_option(c("--transcripts"), default=NULL,
                help="a FASTA file containing the transcript sequences"),
    make_option(c("--geneset"), default=NULL,
                help="a GTF file containing the geneset"),
    make_option(c("--genomeversion"), default=NULL,
                help="e.g. GRCm39"),
    make_option(c("--organism"), default=NULL,
                help="e.g. Mus Musculus"),
    make_option(c("--release"), default=NULL,
                help="corresponding ensembl release eg 110"),
    make_option(c("--samples"), default=NULL,
                help="the txseq samples.tsv file"),
    make_option(c("--outfile"), default="none",
                help="outfile")
    )

opt <- parse_args(OptionParser(option_list=option_list))

print("Running with options:")
print(opt)



out_folder = dirname(opt$outfile)
jsonFile_path = file.path(out_folder,"make.linked.Txome.json")

# set the tximeta cache location
# - this is essential to ensure use of the corrected linked transcriptome
#   (in testing, tximeta repeatedly tried to use incorrect cached files)
setTximetaBFC(file.path(out_folder,"cache"), quiet = FALSE)

message("making Linked Transcriptome")
makeLinkedTxome(indexDir=opt$indexdir,
                source="LocalEnsembl",
                organism=opt$organism,
                release=opt$release,
                genome=opt$genomeversion,
                fasta=opt$transcripts,
                gtf=opt$geneset,
                write=TRUE,
		jsonFile=jsonFile_path)

# construct the coldata

message("making the coldata")
coldata <- read.table(opt$samples, header=T, sep="\t")

coldata$names <- coldata$sample_id
coldata$files <- file.path(getwd(), opt$salmondir, coldata$name, "quant.sf")

write.table(coldata,file.path(dirname(opt$outfile),"coldata.tsv"),
            col.names=T, sep="\t", row.names=F, quote=F)

message("making the se object")
se <- tximeta(coldata)

message("making the gene level summary")
gse <- summarizeToGene(se)

message("saving the result")
saveRDS(list(se=se, gse=gse),
        opt$outfile)
