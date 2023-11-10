#' Helper function for melting a matrix
#' @export
melt_mat <-function(mat, phenoData, plot_color)
    {
    mCD <- melt(mat)
    colnames(mCD) <- c("gene_id", "sample_id", "counts")
    mCD$group <- phenoData[mCD$sample_id, plot_color]
    mCD
}



#' Helper function for plotting densities
#' @export
plotDensities <- function(countMatrix, phenoData, plot_color, plotTitle)
{

    mCD <- melt_mat(log2(countMatrix+1),phenoData,plot_color)
    
    mCD <- mCD[mCD$counts>min(mCD$counts),]
    
    gp1 <- ggplot(mCD, aes_string("counts", group="sample_id", color="group")) + geom_density()
    gp1 <- gp1 + ggtitle(plotTitle) + guides(color=FALSE)
    gp1 <- gp1 + theme_bw()

    
    # row_meds <- apply(countMatrix,1,median)
    # rle <- log2(countMatrix/row_meds)
    
    l2mat <- log2(countMatrix + 1)
    
    rlem <- melt_mat(l2mat, phenoData,plot_color)
    rlem <- rlem[rlem$counts > min(rlem$counts),]
    
    gp2 <- ggplot(rlem, aes_string("sample_id", "counts", group="sample_id", color="group"))
    gp2 <- gp2 + geom_boxplot(outlier.shape=NA)
    gp2 <- gp2 + ggtitle(plotTitle) + theme(axis.title.x=element_blank(),
                                            axis.text.x=element_blank(),
                                            axis.ticks.x=element_blank())
    gp2 <- gp2 + geom_hline(yintercept=0, linetype="dashed")
    gp2 <- gp2 + ylab("Relative log expression (RLE)")
    gp2 <- gp2 + theme_bw()
    gp2 <- gp2 +theme(axis.title.x=element_blank(),axis.text.x=element_blank(), axis.ticks.x=element_blank())


    return(list(den=gp1,bp=gp2))
    }

#' Upper-quartile normalise an expression matrix
#' @param exprs_matrix An expression matrix
#' @export
upperQuartileNormalise <- function(exprs_matrix)
{
    # function to upper quartile normalise a matrix

    uqs <- apply(exprs_matrix, 2, function(x) quantile(x[x>0],0.75))

    uqn <- t(t(exprs_matrix) / uqs) * mean(uqs)

    return(uqn)

    }
