Mouse HSCs example
==================

Introduction
------------

For this example we use paired end RNA-seq data from `Regan-Komito et al 'GM-CSF drives dysregulated hematopoietic stem cell activity and pathogenic extramedullary myelopoiesis in experimental spondyloarthritis' Nature Communicaitons 2020 <https://doi.org/10.1038/s41467-019-13853-4>`_. The data can be retrieved from the European Nucleotide Archive (ENA) under accession `PRJNA521342 <https://www.ebi.ac.uk/ena/browser/view/PRJNA521342>`_.

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, these data are already avaliable in the "/well/kir/projects/mirror/ena/PRJNA521342/" folder.



1. Getting the configuration files
----------------------------------

Clone the folders and files for the example into a suitable local folder: ::

  cp -r /path/to/cellhub/examples/mouse_hscs/* .

This will create 2 folders:

- "indexes" where the Salmon and Hisat indexes can be built if necessary
- "txseq" where the pipelines will be run
- "rmd" where the down-stream analysis with R markdowns is to be performed.

The folders contain the necessary configuration files: please edit the txseq/libraries.tsv file to point to the location of the FASTQ files retrieved from the ENA on your system.


2. Building indexes
-------------------

The example requires Salmon and Hisat2 indexes. If you need to build these, they can be built using txseq pipelines as follows.

To build a salmon index cd into the "indexes/salmon" directory and edit the "pipeline_salmon_index.yml" file as appropriate. The index can then be built with following command: ::

  txseq salmon_index make full -v5

To build a hisat2 index cd into the "indexes/hisat2" directory and edit the "pipeline_hisat_index.yml" file as appropriate. The index can then be built with following command: ::

  txseq hisat_index make full -v5

Please see the documentation for :doc:`pipeline_salmon_index.py <pipelines/pipeline_salmon_index>` and :doc:`pipeline_hisat_index <pipelines/pipeline_hisat_index>` for more details.

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, suitable indexes have already been built and this step should be skipped.

.. note:: It is recommended to use Gencode source files for the Salmon index and Ensembl source files for the Hisat2 index. Please check the Gencode release notes to make sure that you are using the Gencode release that matches the Ensembl version used for Hisat.


3. Setting up 
-------------

Core configuration for txseq pipelines is performed using :doc:`pipeline_setup.py <pipelines/pipeline_setup.py>`. The locations of genome indexes and annotations are specified once in the pipeline_setup.yml configuration file. This yml file is used by the downstream pipelines.

This pipeline:

#. Checks that references are present.

#. Checks the libraries.tsv and samples.tsv input files.

#. Creates additional annotation files for downstream analysis.

To run the pipeline, cd into the "txseq" directory and execute the command: ::

  txseq setup make full -v5 -p10


4. Checking FASTQ read quality
------------------------------
  
