Mouse HSCs example
==================

Introduction
------------

For this example we use paired end RNA-seq data from `Regan-Komito et al 'GM-CSF drives dysregulated hematopoietic stem cell activity and pathogenic extramedullary myelopoiesis in experimental spondyloarthritis' Nature Communicaitons 2020 <https://doi.org/10.1038/s41467-019-13853-4>`_. The data can be retrieved from the European Nucleotide Archive (ENA) under accession `PRJNA521342 <https://www.ebi.ac.uk/ena/browser/view/PRJNA521342>`_.

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, these data are already available in the "/well/kir/projects/mirror/ena/PRJNA521342/" folder.



1. Getting the configuration files and report templates
-------------------------------------------------------

Make a suitable local folder and copy the samples.tsv and libraries.tsv for the "mouse_hscs" example into it. Here we choose to run the example in a folder with the path "~/work/hscs_example" ::

  mkdir ~/work/txseq_hscs_example
  cd ~/work/txseq_hscs_example
  cp -r /path/to/txseq/examples/mouse_hscs/* .
  cp -r /path/to/txseq/reports .
  
Edit the txseq/libraries.tsv file to point to the location of the FASTQ files retrieved from the ENA on your system.


2. Retrieving and preparing annotations 
----------------------------------------

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, the required txseq annotations are available in the mirror folder and this step can be skipped.
  
Follow the instructions on the :doc:`Genomes and Annotations <genomesAndAnnotations>` page to:

#. Retrieve the required sequence and annotation files.

#. Run the "txseq ensembl" pipeline to prepare santitised mouse genome and annotation files for RNA-seq analysis.

  
3 Building the Salmon and Hisat2 transcriptome indexes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, txseq mouse transcriptome indexes have already been built in the mirror folder and this step can be skipped.

The example requires Salmon and Hisat2 indexes. To build these, follow the :doc:`Building transcriptome indexes <buildingTranscriptomeIndexes>` instructions.


4. Checking FASTQ read quality
------------------------------

First we run the `FastQC tool <https://www.bioinformatics.babraham.ac.uk/projects/fastqc/>`_ using :doc:`pipeline_fastqc.py<pipelines/pipeline_fastqc>`. Get a copy of the configuration file and edit appropriately to ensure that the correct "libraries.tsv" and "samples.tsv" files paths are set ::

  cd ~/work/txseq_hscs_example
  mkdir fastqc
  cd fastqc
  txseq fastqc config # get a copy of the default configuration file
  emacs pipeline_fastqc.yml # edit the configuration file as appropriate
  
The pipeline can then be run as follows ::

  txseq fastqc make full -v5 -p20
  
The pipeline parses and store the FastQC output into sqlite database in a file called "csvdb". To visualise the results, open the associated R Markdown Report ("reports/fastqc.Rmd") in Rstudio, assign the location of the database to the "fastqc_sqlite_database" variable and knit the report.


5. Mapping with Hisat2
----------------------

Next we map the data using :doc:`pipeline_hisat.py<pipelines/pipeline_hisat>`. Fetch and edit a copy of the configuration file to set the paths to the "libraries.tsv" and "samples.tsv" files and hisat index ::

  cd ~/work/txseq_hscs_example
  mkdir hisat
  cd hisat
  txseq hisat config # get a copy of the default configuration file
  emacs pipeline_hisat.yml # edit the configuration file as appropriate
  
The pipeline can then be run as follows ::

  txseq hisat make full -v5 -p20

The output BAM files are located in the "hisat.dir" sub-directory.


6. Generating post-mapping QC statistics
----------------------------------------

After mapping with Hisat2, post-mapping QC statistics are computed using :doc:`pipeline_bamqc.py<pipelines/pipeline_bamqc>`. This pipeline runs several `Picard <https://broadinstitute.github.io/picard/>`_ tools including *CollectRnaSeqMetrics*, *EstimateLibraryComplexity*, *AlignmentSummaryMetrics* and *CollectInsertSizeMetrics* as well as some custom scripts. ::

  cd ~/work/txseq_hscs_example
  mkdir bamqc
  cd bamqc
  txseq bamqc config # get a copy of the default configuration file
  emacs pipeline_bamqc.yml # edit the configuration file as appropriate
  
The pipeline can then be run as follows ::

  txseq bamqc make full -v5 -p20

The results are saved in an sqlite database in the "csvdb" file. 


7. Quantitation with FeatureCounts
----------------------------------

Count tables can be extracted from the BAM file using :doc:`pipeline_feature_counts.py<pipelines/pipeline_feature_counts>`. ::

  cd ~/work/txseq_hscs_example
  mkdir feature_counts
  cd feature_counts
  txseq feature_counts config # get a copy of the default configuration file
  emacs pipeline_feature_counts.yml # edit the configuration file as appropriate

The pipeline can then be run as follows ::

  txseq feature_counts make full -v5 -p20

The results are saved in an sqlite database in the "csvdb" file. 


8. Quantitation with Salmon
---------------------------

To quantitate the data using :doc:`pipeline_salmon.py<pipelines/pipeline_salmon>`, we begin by fetching and edit a copy of the configuration file to set the paths to the "libraries.tsv" and "samples.tsv" files and salmon index ::

  cd ~/work/txseq_hscs_example
  mkdir salmon
  cd salmon
  txseq salmon config # get a copy of the default configuration file
  emacs pipeline_salmon.yml # edit the configuration file as appropriate
  
The pipeline can then be run as follows ::

  txseq salmon make full -v5 -p20

The results of the pipeline are stored in the "csvdb" sqlite database and as a tximeta object in the "tximeta.dir/tximeta.RDS" for downstream analysis. Flat tables of TPMs can be retrieved from the database or from the "salmon.dir/salmon.transcripts.tpms.txt.gz" file.


9. Post-mapping QC analysis
---------------------------

After running :doc:`pipeline_bamqc.py<pipelines/pipeline_bamqc>` and :doc:`pipeline_salmon.py<pipelines/pipeline_salmon>` post-mapping QC can be performed using the "post_mapping_qc.Rmd" report template.

Make a copy of the Rmd template file and open it in Rstudio to perform the analysis. The report visualises the individual QC statistics and performs a correlation analysis of the QC statistics with gene-expression space principle-components.

This analysis helps to identify confounding technical sources of variation.


10. Exploratory analysis
-----------------------

After running :doc:`pipeline_salmon.py<pipelines/pipeline_salmon>` the similarity between the samples in gene-expression space can be explored using the "exploratory_data_analysis.Rmd" R Markdown report template.

Make a copy of this file and open it in Rstudio to perform the analysis. The report produces plots showing hierarchical clustering of the samples by correlation of their expression profiles, the results of principle components analysis and a UMAP project of the samples.

Together with the post-mapping QC report this analysis is useful for the identification of outliers.


11. DESeq2 analysis
-------------------


After running :doc:`pipeline_salmon.py<pipelines/pipeline_salmon>` differential expression analysis can be performed using the "differential_expression.Rmd" R Markdown report template.

Make a copy of this file and open it in Rstudio to perform the analysis. 
