#' Make a histogram of gene expression levels
#' @export
expression_hist <- function(count_matrix,title="")
    {
    zero <- min(count_matrix)
    notAllZero <- (rowMeans(count_matrix)> zero)
    fcm <- count_matrix[notAllZero,]
    fcm[fcm==zero] <- NA
    mcm <-melt(fcm)
    gp <- ggplot(mcm, aes(value,colour=X2)) + geom_density()
    gp <- gp + ggtitle(title) + xlab("") # + xlim(lim)
    gp <- gp + theme(legend.position="none")
    gp <- gp + theme_bw()
    return(gp)
}

#' Make a correlation heatmap
#' @export
plot_cor <- function(m, mar=c(14,14)) 
  {heatmap.2(m, 
    trace="none",
    key.xlab = paste(distance_method),
    key.ylab = "",
    col=l$col,
    breaks=l$breaks,
    density.info=c("none"),
    mar=mar)}    

#' Function to compute correlation based on non-zero values
cor_nz <- function(m, min_exprs=0, method="pearson")
{
  j <- dim(m)[2]
  r <- matrix(ncol=j, nrow=j)
  for(x in c(1:j))
  {
    for(y in c(x:j))
    {
      m2 <- m[,c(x,y)]
      m2 <- m2[apply(m2,1,max)>=min_exprs,]
      c <- cor(m2[,1],m2[,2], method=method)
      r[x,y] <- c
      r[y,x] <- c
    }
  }
  rownames(r) <- colnames(m)
  colnames(r) <- colnames(m)
  r
}

#' Function to get colors for a heatmap
#' @param mat the data matrix
#' @param lower_quantile the quantile to use for the lowest break
#' @param upper_quantile the quantile to use for the highest break
#' @param nbreaks the number of breaks
#' @param palette An RColorBrewer palette
#' 
#' @export
#' 
get_col <- function(mat,
                    lower_quantile=0,
                    upper_quantile=0.9,
                    nbreaks=50,
                    palette=brewer.pal(9, name="YlOrRd"))
{
  require(RColorBrewer)
    low <- quantile(mat,lower_quantile)
    high <- quantile(mat,upper_quantile)
    breaks=seq(low,high,(high-low)/nbreaks)
    col=colorRampPalette(palette)
    return(list(breaks=breaks,col=col))
}