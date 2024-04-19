.. txseq documentation master file.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

txseq
=====

Txseq provides a suite of modular workflows for the QC and analysis of bulk RNA-sequencing data on high-performance compute clusters. These include pipelines for sanitising Ensembl annotations for RNA-seq analysis, building transcriptome indexes and performing quality control with Fastqc and Picard tools. Pipelines for traditional alignment-based mapping with Hisat2 and quantitation with featureCounts are provided along with a more-modern pseudo-alignment workflow that incorporates Salmon and tximeta. Template reports for sequence quality, post-mapping qc analysis, exploratory data analysis and differential gene expression are provided as Rmarkdown notebooks. 


.. toctree::
   :maxdepth: 1

   overview.rst
   installation.rst
   genomesAndAnnotations.rst
   buildingTranscriptomeIndexes.rst
   usage.rst
   mouse_hscs_example.rst
   pipelines.rst
   tasks.rst
   contributing.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
