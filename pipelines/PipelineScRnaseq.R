normalise_to_spikes <- function(spikes,
                                all_exprs,
                                exprs_col="FPKM",
                                plotname,
                                outfile,
                                track)
{
    ## exprs_col is a column of "all_exprs" that contains a
    ## length-normalised expression estimate, i.e. FPKM or TPM

    ## remove spikes with zero fpkm, add 1, log 10 transform
    goodSpikes <- spikes[spikes[[exprs_col]]!=0,]

  copies = log10(goodSpikes$copies_per_cell + 1)
  exprs = log10(goodSpikes[[exprs_col]] + 1 )

  ##get fit
  fit = lm(copies ~ 0 + exprs + I(exprs^2), list(copies,exprs))

  #make diagnostic plot of fit.
  pdf(plotname)
  plot(log10(spikes[[exprs_col]]+1),log10(spikes$copies_per_cell+1),
       main=track,
       xlab=paste("Spike in", exprs_col, "+ 1 (log10)"),
       ylab="Spike in copy number + 1 (log10)")
  plot_data = data.frame(exprs_col=sort(log10(spikes[[exprs_col]]+1)))
  lines(plot_data[[exprs_col]],predict(fit,plot_data),col="red")
  dev.off()

  #calculate copies per cell from the raw (length-normalised) expression values**
  exprs_values = data.frame(exprs_col=log10(all_exprs[[exprs_col]]+1), gene_id=all_exprs$gene_id)

  transformed_copy_number = predict(fit,exprs_values)

  copy_number = 10^transformed_copy_number - 1
  raw_exprs = 10^exprs_values$exprs_col - 1

  normalised = data.frame(gene_id = exprs_values$gene_id,
                          copy_number = copy_number,
                          exprs_col = raw_exprs)

  names(normalised)[names(normalised) == "exprs_col"] <- exprs_col

  write.table(normalised, outfile, row.names=F,sep="\t",quote=F)

}
