stopifnot(
    require(devtools),
    require(BiocManager))


install.package <- function(x, source="CRAN", github_repo="")
{
    pkg <- x

    if (!require(pkg, character.only = TRUE))
    {
        message("installing missing package: ", pkg)

        if(source=="CRAN")
            {
                install.packages(pkg, dep=TRUE)

            } else if (source=="bioconductor")
            {
                BiocManager::install(pkg)

            } else if (source=="github")
            {
                install_github(github_repo)
            }

        if(!require(pkg,character.only = TRUE)) stop("Package not found")

    }
}

cran_packages <- c(
"cba",
"RSQLite",
"DBI",
"RColorBrewer",
"dplyr",
"fastcluster",
"ggplot2",
"ggrastr",
"gplots",
"hexbin",
"knitr",
"markdown",
"openxlsx",
"bookdown",
"optparse",
"pander",
"psych",
"reshape2",
"umap"
)

bioconductor_packages <- c(
"apeglm",
"ComplexHeatmap",
"dendsort",
"genefilter",
"ggrepel",
"gridExtra",    
"tximeta",
"DESeq2",
"vsn"
)

github_packages <- c("gsfisher"="sansomlab/gsfisher")


message("installing cran packages")
for(x in cran_packages)
{
    install.package(x, source="CRAN")
}

message("installing bioconductor packages")
for(x in bioconductor_packages)
{
    install.package(x, source="bioconductor")
}

message("installing github packages")
for(x in names(github_packages))
{
    install.package(x, source="github", github_repo=github_packages[x])
}
