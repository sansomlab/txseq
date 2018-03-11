## A script to estimate compute copy numbers based on:
## (1) A set of spike-ins for which the copy numbers are given
## (2) A table of length normalised expression values

## options.


library(optparse)

## deal with the options
option_list <- list(
    make_option(c("--spikeintable"), default="must_specify",
                help="A tab-delimeted text-file containing the spike in information"),
    make_option(c("--spikeidcolumn"), default="gene_id",
                help="the name of the column in the spikeinfo table containing the spike-in identifier"),
    make_option(c("--spikecopynumbercolumn"), default="seurat.out.dir",
                help="the name of the column in the spikeinfo table contining the known copy numbers"),
    make_option(c("--exprstable"), default="must_specify",
                help="A tab-delimited table containing length normalised expression tables. One column per sample. One identifier column."),
    make_option(c("--exprsidcolumn"), default="none",
                help="The name of the identifer column in the expression table"),
    make_option(c("--outfile"), default="none",
                help="The name of the file to write the results to")
)

opt <- parse_args(OptionParser(option_list=option_list))

print("Running with options:")
print(opt)

## read in the spike in information

spikes <- read.table(opt$spikeintable, as.is=T, header=T, sep="\t")
rownames(spikes) <- spikes[[opt$spikeidcolumn]]
spikes[[opt$spikeidcolumn]] <- NULL


## read in the expression table

exprs <- read.table(opt$exprstable, as.is=T, header=T, sep="\t")
rownames(exprs) <- exprs[[opt$exprsidcolumn]]
exprs[[opt$exprsidcolumn]] <- NULL

non_spike_ids <- rownames(exprs)[!rownames(exprs) %in% rownames(spikes)]

results <- data.frame(row.names=non_spike_ids)
results[[opt$exprsidcolumn]] <- non_spike_ids

for(sample in colnames(exprs))
{

    goodSpikes <- intersect(rownames(exprs[exprs[[sample]]!=0,]),
                            rownames(spikes))

    spike_copies <- log10(spikes[goodSpikes,opt$spikecopynumbercolumn] + 1)
    obs_exprs <- log10(exprs[goodSpikes, sample] + 1)

    ## get the fit
    fit = lm(spike_copies ~ 0 + obs_exprs + I(obs_exprs^2), list(spike_copies,obs_exprs))

    ## make diagnostic plot showing the fit.
    plotname = paste(gsub(".txt","",opt$outfile),sample,"pdf",sep=".")
    pdf(plotname)

    plot(log10(exprs[rownames(spikes), sample]+1),
         log10(spikes[[opt$spikecopynumbercolumn]]+1),
         main=sample,
         xlab="Spike in expression level log10(x+1)",
         ylab="Spike in copy number log10(x+1)")

    plot_data = data.frame(obs_exprs=sort(log10(exprs[rownames(spikes), sample]+1)))

    lines(plot_data$obs_exprs,predict(fit,plot_data),col="red")

    dev.off()

    ## calculate copies per cell from the raw (length-normalised) expression values**
    exprs_values = log10(exprs[non_spike_ids, sample]+1)

    transformed_copy_number = predict(fit,data.frame(obs_exprs=exprs_values))

    copy_number = 10^transformed_copy_number - 1

    results[[sample]] <- copy_number

    }

## save the results to a tab-delimited text-file
write.table(results, opt$outfile, col.names=TRUE,
            sep="\t", row.names=FALSE, quote=FALSE)
