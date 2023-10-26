#' Get interesting genes...
#' @export
get_interesting <- function(tt,
                    p_value_threshold = 0.05,
                    n=10,
                    id_col = "gene_id",
                    p_col="padj", 
                    fc_col="log2FoldChange")
{
  # function to return the "most interesting" genes from a top table
  # genes are ranked by (i) p-value and (ii) fold change
  # and the top n genes taken for each ranking factor
  # for each direction (up and down-regulated)

  # subset to significant gene
  tt <- tt[tt[[p_col]] < p_value_threshold & !is.na(tt[[p_col]]),]
  # set the direction
  tt$direction <- "down"
  tt$direction[tt[[fc_col]] > 0] <- "up"
  take <- c()
  
  for(dir in c("down", "up"))
  {
    # subset to direction of interest
    tmp <- tt[tt$direction == dir,]
    # compute the number of rows we can take
    ntake <- min(n,nrow(tmp))
    
    # take by p-value
    tmp <- tmp[order(tmp[[p_col]]),]
    take <- c(take, tmp[[id_col]][1:ntake])
    
    # take by fold-change
    tmp <- tmp[rev(order(abs(tmp[[fc_col]]))),]
    take <- c(take, tmp[[id_col]][1:ntake])

  }
  
  # subset to unique gene_ids
  take <- unique(take)
  
  return(take)
}

#' deseq2 independent filtering plot.
#' @export
if_plot <- function(res) 
{
  plot(metadata(res)$filterNumRej,
       type="b", ylab="number of rejections",
       xlab="quantiles of filter")
  lines(metadata(res)$lo.fit, col="red")
  abline(v=metadata(res)$filterTheta)
}

#' plot deseq2 size factors.
#' @export
plot_size_factors <- function(dds, nick)
{
  SFs <- sizeFactors(dds)
  size_df <- as.data.frame(SFs,drop=F)
  s <- rownames(size_df)
  size_df$samples <- factor(s, levels=s[order(size_df$SFs)])
  
  gp <- ggplot(size_df, aes(samples, SFs)) + geom_bar(stat="identity")
  gp <- gp + theme(axis.text.x = element_text(angle = 90, hjust = 1)) + xlab("")
  gp <- gp + ylab("size factor")
  return(gp)
}

#' make MA and volcano plots from DESeq2 object
#' @export
de_plots <- function(tt, 
                    interesting_genes=NULL,
                    p_value_threshold=0.05,
                    p_col="padj",
                    fc_col="log2FoldChange",
                    exprs_col="baseMean",
                    label="gene_name",
                    title= NULL,
                    abs_fc_threshold=2,
                    log_x=T)
{
  require(ggrepel)
  
  # add transformed p value column for volcano
  tt$vp <- -log10(tt[[p_col]])
  
  #  split top table by signficance and fold change.
  ttns <- tt[tt[[p_col]]>0.05 | abs(tt[[fc_col]]) < log2(abs_fc_threshold),]
  tts <- tt[tt[[p_col]]<=0.05 & abs(tt[[fc_col]]) >= log2(abs_fc_threshold),]
  
  xmin=min(tt[[exprs_col]])
  xmax=max(tts[[exprs_col]]) * 1.2
  
  ttslfc <- tts[rev(order(abs(tts[[fc_col]]))),]
  ttsexpr <- tts[rev(order(tts[[exprs_col]])),]
  
  tts_label <- tts[interesting_genes,]
  
  # abs log2 fc threshold
  abs_fc <- log2(abs_fc_threshold)

  # make the ma plot
  gp <- ggplot(ttns, aes_string(exprs_col, fc_col))
  gp <- gp + geom_point(data=ttns, alpha=0.4, color="grey")
  gp <- gp + geom_point(data=tts, color="red", alpha=0.6)
  
  gp <- gp + geom_text_repel(data=tts_label, aes_string(label=label))

  gp <- gp + geom_hline(yintercept=c(-abs_fc,abs_fc), 
                        linetype="dashed",color="darkgrey")
  gp <- gp + geom_hline(yintercept=c(0), linetype="solid",color="darkgrey")
  
  if(log_x) { gp <- gp + scale_x_continuous(trans="log2", limits=c(xmin,xmax))}
  else { gp <- gp + xlim(xmin,xmax)}
  gp <- gp + xlab("average expression (log2)")
  gp <- gp + ylab("log2 fold change")
  if(!is.null(title)) { gp <- gp + ggtitle(title) }

    
  # make the volcano plot
  vp <- ggplot(ttns, aes_string(fc_col, "vp"))
  vp <- vp + geom_point(data=ttns, alpha=0.4, color="grey")
  vp <- vp + geom_point(data=tts, color="red", alpha=0.6)
  
  vp <- vp + geom_text_repel(data=tts_label, aes_string(label=label))
  
  vp <- vp + geom_hline(yintercept=c(-log10(0.05)), linetype="dashed",color="darkgrey")
  
  vp <- vp + geom_vline(xintercept=c(-abs_fc,abs_fc), linetype="dashed",color="darkgrey")
  vp <- vp + geom_vline(xintercept=c(0), linetype="solid",color="darkgrey")
  
  vp <- vp + xlab("Fold change, log2(n+1)")
  vp <- vp + ylab("- log10(adjusted p-value)")
  if(!is.null(title)) { vp <- vp + ggtitle(title) }
  
  return(list(ma=gp,volcano=vp))
}


#' Make a heatmap of DE genes
#' @export
de_heatmap <- function(exprs_matrix,
                      interesting_genes,
                      annotation,
                      key_label="expression level",
                      mar=c(10,10),
                      cexRow=1,
                      cexCol=1)
{

  m <- exprs_matrix[rownames(exprs_matrix) %in% interesting_genes,]

  m <- as.matrix(log10(m + 1))

  row_names <- annotation[rownames(m),"gene_name"]

  colden = get_den(t(m),
                 dist_method="minkowski",
                 clust_method="complete",
                 optimize=T)

  hm <- function() {
  rnaseq_heatmap(m,
                 rowden=T,
                 colden=F,
                 labRow=row_names,
                 key.xticks=c(1:4),
                 key.xlab=key_label,
                 log_factor=10,
                 mar=mar,
                 cexRow=cexRow,
                 cexCol=cexCol)
}

hm()
}

#' Function for preparing a DESeq2 object
#' @export
setup_dds <- function(counts, 
                      columnData,
                      subset= NULL, 
                      design = NULL,
                      reference_levels = NULL)
{
 
  # setup a DESeq2 object for testing
  if(!is.null(subset))
  {
    # subset the count matrix and columnData
    columnData <- sample_info[sample_info$sample_id %in% subset,]
    counts <- as.matrix(counts[,subset])
    message("subsetting active")
  }
  
  if(any(rownames(columnData) %in% colnames(counts)) == FALSE)
  {
    stop("Sample information missing from columnData")
  }
  
  # reorder the columnData to match the count matrix:
  columnData <- columnData[colnames(counts),]
  
  if(is.null(design)) 
  { 
    stop("the design must be specificied")
    }
  
  message("building the DESeq2 object")
  # build the DESeq2 object
  
  dds <- DESeqDataSetFromMatrix(countData=counts, 
                                colData=columnData, 
                                design=as.formula(design))
  
  
  if(!is.null(reference_levels))
  {
    message("setting reference levels")
    # After re-leveling fold changes will be relative to the 
    # specified reference level
    for(given_factor in names(reference_levels))
    {
      ref_level <- reference_levels[[given_factor]]
      if(!is.factor(dds[[given_factor]])) 
      { 
        dds[[given_factor]] <- factor(dds[[given_factor]])
      }
  
      if(ref_level %in% levels(dds[[given_factor]]))
      {
        dds[[given_factor]] <- relevel(dds[[given_factor]], ref_level)
      } else {
        warning(paste(ref_level, "not found in", given_factor,"; factor is not relevelled"))
      }
    }
  }
  dds
}

#' Function for running a DESeq2 test.
#' @export
run_deseq2 <- function(dds, name = "placeholder",
                       location_function="median", fit_type="local",
                       contrast,
                       id_col = "gene_id",
                       annotation = ann_df)
{
  
  # run a differentially expression test using a prepared object.
  dds <- estimateSizeFactors(dds, locfunc=match.fun(location_function))
  dds <- estimateDispersions(dds, fitType=fit_type)
  dds <- nbinomWaldTest(dds)

  raw_res <- results(dds, contrast)
  
  # convert to data frame after if_plot!
  res <- data.frame(raw_res)
  res <- res[!is.na(res$padj),]
  
  # sort by FDR
  res <- res[order(res$padj),]
  
  # add the gene gene_names to the results
  res$gene_name = annotation[rownames(res), "gene_name"]
  res[[id_col]] <- rownames(res)
  
  # reorder the columns 
  c1 <- c("gene_id","gene_name")
  c2 <- colnames(res)[!colnames(res) %in% c1]
  res <- res[,c(c1,c2)]

  res <- list(table=res, dds=dds, res=raw_res)
}