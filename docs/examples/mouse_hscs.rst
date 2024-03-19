Mouse HSCs example
==================

Introduction
------------

For this example we use paired end RNA-seq data from `Regan-Komito et al 'GM-CSF drives dysregulated hematopoietic stem cell activity and pathogenic extramedullary myelopoiesis in experimental spondyloarthritis' Nature Communicaitons 2020 <https://doi.org/10.1038/s41467-019-13853-4>`_. The data can be retrieved from the European Nucleotide Archive (ENA) under accession `PRJNA521342 <https://www.ebi.ac.uk/ena/browser/view/PRJNA521342>`_.

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, these data are already avaliable in the "/well/kir/projects/mirror/ena/PRJNA521342/" folder.



1. Getting the configuration files
----------------------------------

Clone the folders and files for the example into a suitable local folder: ::

  cp -r /path/to/txseq/examples/mouse_hscs/* .

Edit the txseq/libraries.tsv file to point to the location of the FASTQ files retrieved from the ENA on your system.


2. Preparing annotations and transcriptome indexes
--------------------------------------------------

.. note:: If you are working in the Kennedy workspace on the Oxford BMRC cluster, suitable indexes have already been built and this step should be skipped.

#. Fetching ensembl annotations



The example requires Salmon and Hisat2 indexes. If you need to build these, they can be built using txseq pipelines as follows.

To build a salmon index cd into the "indexes/salmon" directory and edit the "pipeline_salmon_index.yml" file as appropriate. The index can then be built with following command: ::

  txseq salmon_index make full -v5

To build a hisat2 index cd into the "indexes/hisat2" directory and edit the "pipeline_hisat_index.yml" file as appropriate. The index can then be built with following command: ::

  txseq hisat_index make full -v5







3. Setting up 
-------------



4. Checking FASTQ read quality
------------------------------
  
