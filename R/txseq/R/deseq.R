#' Group-aware pre-filtering of a DESeq object.
#' This function is used to filter out genes that do not pass a minimum
#' expression level in a minimum number of replicates from at least 1 group.
#'
#' @param dds A DESeq2 dataset object
#' @param grouping_var The name of the variable in the colData that contains the experimental groups
#' @param min_replicates The minimum number of replicates within a group that have min_counts
#' @param min_counts The minimum number counts
#'
#' @export
filterDESeqDatasetByGroup <- function(dds, grouping_var="condition", min_replicates=2, min_counts=10)
{
  message("number of genes in input dds: ", nrow(counts(dds)))
  groups <- unique(colData(dds)[[grouping_var]])
  
  message("performing filtering on groups: ",paste(groups,collapse=", "))
  group_test_results <- data.frame(row.names=rownames(counts(dds)))
  for(group in groups)
  {
    message("working on group: ",group)
  
    samples <- colData(dds)$sample_id[colData(dds)[[grouping_var]]==group]
    message("...with samples: ", paste(samples,collapse=", "))
  
    group_test_results[[group]] <- apply(counts(dds)[,samples],1,function(x) length(x[x>=min_counts])>=min_replicates)
  }

  keep <- as.vector(apply(group_test_results,1,function(x) any(x)))

  dds <- dds[keep,]
  message("number of genes in filtered dds: ", nrow(counts(dds)))
  
  dds
}


#' A function to return genes of interest from a DESeq2 top table.
#' Genes are ranked by (i) p-value and (ii) fold change
#' and the top n genes taken for each ranking factor
#' for each direction (up and down-regulated)''
#' 
#' @export
get_interesting <- function(tt,
                    p_value_threshold = 0.05,
                    n=10,
                    id_col = "gene_id",
                    p_col="padj", 
                    fc_col="log2FoldChange")
{


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
#'
#' importFrom DESeq2 sizeFactors
#'
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
#'
#' @import ggplot2
#' @import ggrepel
#'
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

  
  tt <- tt[!is.na(tt[[p_col]]),]
  
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
  gp <- gp + theme_light()
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
  vp <- vp + theme_light()
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