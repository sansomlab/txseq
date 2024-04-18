#' Make PCA plots using ggplot
#'
#' @import  ggplot2
#' @import  gridExtra
#'
#' @export
ggplot_prcomp <- function(prcomp_object,
                         plots=list("A"=c("PC1","PC2"), "B"=c("PC3","PC4"), "C"=c("PC5","PC6")),
                         sample_information="none",
                         color="c()",
                         shape="c()",
                         label="none",
                         size=3,
                         nudge_scale_factor=40)
{
    pca = prcomp_object

    # sample_information should have the same rownames as pca$x
    pvs <- summary(pca)$importance["Proportion of Variance",]

    names = paste(names(pvs)," (",round(pvs,2),")",sep="")

    #scree plot
    fs <- data.frame(x=c(1:length(names(pvs))), y=as.vector(pvs))

    pcdf <- as.data.frame(pca$x)
    pcdf <- merge(pcdf, sample_information, by=0, all=T)

    gps = list()

    scree <- ggplot(fs, aes(x,y)) + geom_point(size=3) 
    scree <- scree  + xlab("principal component") + ylab("proportion of variance") + ggtitle("scree plot")
    scree <- scree + theme_bw()

    c_lab <- function(props, C)
         {
             return(paste(C, " (", props[[C]]*100,"%)",sep=""))
                 }

    for(plot in names(plots))
        {

            comps <- plots[[plot]]

            PCX <- comps[1]

            PCY <- comps[2]


            nudge_x <- diff(range(pcdf[[PCX]]))/nudge_scale_factor
            nudge_y <- diff(range(pcdf[[PCY]]))/nudge_scale_factor

            gp <- ggplot(pcdf, aes_string(PCX, PCY, color=color, shape=shape))


            if(label!="none")
                {
                    gp <- gp + geom_text(aes_string(label=label), nudge_x=nudge_x, nudge_y=nudge_y, color="darkgrey")
                }

            gp <- gp + geom_point(size=size)
            gp <- gp + xlab(c_lab(pvs,PCX)) + ylab(c_lab(pvs,PCY))
            gp <- gp + theme_bw()

            gps[[plot]] <- gp

        }

    gps[["scree"]] <- scree

    return(gps)

}
