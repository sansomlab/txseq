#' function to draw a heatmap with colored clusters
#' @param clust An object with m=matrix, den_genes=gene dendrogram, den_samples = sample dendrogram
#' @param title Title
#' @param k The number of clusters
#' @param min_size The minimum size
#' 
#' @export
#' 
labelClusters <-function(clust, title, k=10, min_size=100)
{

    #Set up a color scale - could also use min/max instead of quantile.
    low <- quantile(clust$matrix,0.0)
    high <- quantile(clust$matrix,0.9)

    nbreaks=200 # number of graduations
    breaks=seq(low,high,(high-low)/nbreaks) #range (-2 -> 2) and breakpoint size = range_size / no. graduations
    colors=colorRampPalette(c("black","yellow","red"))(nbreaks) # get the color pallete

    # cut the tree
    groups <- cutree(clust$hclust_genes, k=k)
    clust_membership <- as.vector(groups[rownames(clust$m)])

    member_count <- table(clust_membership)
    small_groups <- names(member_count[member_count<min_size])

    clust_membership[clust_membership %in% small_groups] <- "0"

    cluster_names <- unique(as.vector(clust_membership))

    col_pal <- c("grey","yellow","green",
                 "red","blue","black","cyan",
                 "pink","brown","orange",
                 "purple","darkblue")

    rCi <- col_pal[1:length(cluster_names)]

    names(rCi) <- cluster_names[order(cluster_names)]

    rowCols <- as.vector(rCi[clust_membership])
    col_assign <- data.frame(row.names=rownames(clust$m), cluster=rowCols)
    #names(col_assign) <- rownames(clust$m)

    # Plot a heatmap in which the genes and samples are ordered according
    # to the computed clustering
    # see ?heatmap.2
    heatmap.2(clust$m,
              Rowv=clust$den_genes,
              Colv=clust$den_samples,
              trace="none",
              col=colors,
              breaks=breaks,
              labRow=F,
              RowSideColors=rowCols,
              keysize=0.4,
              key.title=NA,
              key.ylab=NA,
              key.xlab="expression (log2)",
              mar=c(17,8),
              #lmat=matrix(c(4,2),nrow=2),
              lhei=c(0.3,2.2),
              lwid=c(0.6,2),
              dendrogram="column",
              main=title
             )

    return(col_assign)
}


#' Version of parPvclust() with optimised leaf ordering
#' # e.g. to execute a clustering in parallel
#' # library(snow)
#' # cl <- makeCluster(12, type="SOCK")
#' #
#' # pvclust.result <- parPvclust(cl, data.matrix,
#' #                           method.dist="correlation",
#' #                           method.hclust="average",
#' #                           nboot=1000)
#' # stopCluster(cl)
#' @param cl Snow cluster
#' @param data The data matrix 
#' @param method.hclust The hclust method
#' @param method.dist The distance method
#' @param use.cor For computing correlation distance
#' @param nboot The number of bootstraps (for pvclust)
#' @param r A sequence.
#' @param store pvclust arg
#' @param weight pvclust arg
#' @param init.rand pvclust arg
#' @param iseed pvclust arg
#' @param quiet pvclust arg
#' 
#' @export
#' 
parPvclust_opt <- function(cl=NULL, data, method.hclust="average",
                           method.dist="correlation", use.cor="pairwise.complete.obs",
                           nboot=1000, r=seq(.5,1.4,by=.1), store=FALSE, weight=FALSE,
                           init.rand=NULL, iseed=NULL, quiet=FALSE)
{

    require(cba)
    pkg.ver <- parallel::clusterCall(cl, packageVersion, pkg = "pvclust")
    r.ver <- parallel::clusterCall(cl, getRversion)
    if (length(unique(pkg.ver)) > 1 || length(unique(r.ver)) >
        1) {
        node.name <- parallel::clusterEvalQ(cl, Sys.info()["nodename"])
        version.table <- data.frame(node = seq_len(length(node.name)),
            name = unlist(node.name), R = unlist(lapply(r.ver,
                as.character)), pvclust = unlist(lapply(pkg.ver,
                as.character)))
        if (nrow(version.table) > 10)
            table.out <- c(capture.output(print(head(version.table,
                n = 10), row.names = FALSE)), "    ...")
        else table.out <- capture.output(print(version.table,
            row.names = FALSE))
        warning("R/pvclust versions are not unique:\n", paste(table.out,
            collapse = "\n"))
    }
    if (!is.null(init.rand))
        warning("\"init.rand\" option is deprecated. It is available for back compatibility but will be unavailable in the future.\nSpecify a non-NULL value of \"iseed\" to initialize random seed.")
    if (!is.null(iseed) && (is.null(init.rand) || init.rand))
        parallel::clusterSetRNGStream(cl = cl, iseed = iseed)
    n <- nrow(data)
    p <- ncol(data)
    if (is.function(method.dist)) {
        distance <- method.dist(data)
    }
    else {
        distance <- pvclust:::dist.pvclust(data, method = method.dist,
            use.cor = use.cor)
    }
    data.hclust <- hclust(distance, method = method.hclust)


    co <- order.optimal(distance,
                        data.hclust$merge)

    data.hclust$merge <- co$merge
    data.hclust$order <- co$order


    if (method.hclust == "ward" && getRversion() >= "3.1.0") {
        method.hclust <- "ward.D"
    }
    size <- floor(n * r)
    rl <- length(size)
    if (rl == 1) {
        if (r != 1)
            warning("Relative sample size r is set to 1.0. AU p-values are not calculated\n")
        r <- list(1)
    }
    else r <- as.list(size/n)
    ncl <- length(cl)
    nbl <- as.list(rep(nboot%/%ncl, times = ncl))
    if ((rem <- nboot%%ncl) > 0)
        nbl[1:rem] <- lapply(nbl[1:rem], "+", 1)
    if (!quiet)
        cat("Multiscale bootstrap... ")
    mlist <- parallel::parLapply(cl, nbl, pvclust:::pvclust.node, r = r,
        data = data, object.hclust = data.hclust, method.dist = method.dist,
        use.cor = use.cor, method.hclust = method.hclust, store = store,
        weight = weight, quiet = quiet)
    if (!quiet)
        cat("Done.\n")
    mboot <- mlist[[1]]
    for (i in 2:ncl) {
        for (j in 1:rl) {
            mboot[[j]]$edges.cnt <- mboot[[j]]$edges.cnt + mlist[[i]][[j]]$edges.cnt
            mboot[[j]]$nboot <- mboot[[j]]$nboot + mlist[[i]][[j]]$nboot
            mboot[[j]]$store <- c(mboot[[j]]$store, mlist[[i]][[j]]$store)
        }
    }
    result <- pvclust:::pvclust.merge(data = data, object.hclust = data.hclust,
        mboot = mboot)
    return(result)
}


#' function to return a cluster dendrogram
#' with optional optimised leaf order.
#' @export
get_den <- function(m,
                    optimize=F,
                    dist_method="manhattan",
                    clust_method="complete",
                    p=1.5)
    {

    require(fastcluster)

    if(dist_method=="cor" | dist_method=="correlation")
        {
        dissym <- (1 - cor(m))/2
        d <- as.dist(dissym)
        }
    else {if(dist_method=="minkowski") {
            d <- dist(m, method=dist_method, p=p)
            }
          else {
              d <- dist(m[,], method=dist_method)
            }
         }

    h <- hclust(d, method=clust_method)

    if(optimize)
    {
      require(cba)
    co <- order.optimal(d, h$merge)

    # overwrite the hclust object with the optimal leaf order
    h$merge <- co$merge
    h$order <- co$order
    }

    as.dendrogram(h)
   }


#' function to draw heatmap from RNA-seq counts or FPKMS
#' @export
rnaseq_heatmap <- function(m,
                           rowden=F,
                           colden=F,
                           labRow=NULL,
                           ramp_colors=c("black","blue","white","yellow","orange","red","brown"),
                           key.xticks=c(1:4),
                           key.xlab="expression level",
                           log_factor=10,
                           mar=c(14,12),
                           title=NULL,
                           lhei=c(1.15,4),
                           lwid=c(1.3,4),
                           cexRow=1,
                           cexCol=1,
                           ...
                           )
{

  nbreaks=200 # number of graduations
  rm <- range(m)
  breaks=seq(rm[1],rm[2],diff(rm)/nbreaks) #range (-2 -> 2) and breakpoint size = range_size / no. graduations
  colors=colorRampPalette(ramp_colors)(nbreaks) # get the color pallete

  heatmap.2(m,
            col=colors,
            breaks=breaks,
            scale="none",
            Rowv=rowden,
            Colv=colden,
            mar=mar,
            trace="none",
            colsep=c(seq(1,dim(m)[2],1)),
            sepwidth=c(0.02,0.02),
            key.title = "",
            #lmat = rbind(c(0,3),c(2,1),c(0,4)),
            key.par=list(mar=c(5.5,.3,5.5,.3)),
            #key.ytickfun = "",
            key.xtickfun = function()
                 {
                    int=key.xticks
                    at = int / max(m)
                    labels = as.character(log_factor^int)
                    return(list(labels=labels, at=at))
                 },
            density.info=c("none"),
            lwid = lwid,
            lhei = lhei,
            key.xlab = key.xlab,
            key.ylab = "",
            labRow = labRow,
            main=title,
            cexRow = cexRow,
            cexCol = cexCol
    )
    }
