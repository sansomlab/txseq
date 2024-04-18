Workflow Overview
=================

Introduction
------------

txseq is designed to efficiently parallelise the processing of bulk RNA-sequencing data on compute clusters. Data for each of the sequencing libraries in the experiment is quantitated and quality controlled in parallel.

The workflow can start from either FASTQ or BAM inputs.

1. Assessment of read quality
------------------------------

Read quality can be assessed using the `FASTQC quality control tool <https://www.bioinformatics.babraham.ac.uk/projects/fastqc/>`_ with :doc:`pipeline_fastqc.py <pipelines/pipeline_fastqc>`.

2. Mapping and Quantitation
---------------------------

Txseq supports the following workflows:

#. `Salmon <https://github.com/COMBINE-lab/salmon>`_ for pseudoalignment (see :doc:`pipeline_salmon.py <pipelines/pipeline_salmon>` for more details).

#. `Hisat2 <http://daehwankimlab.github.io/hisat2/>`_ and the featureCounts `Subread package <https://subread.sourceforge.net>`_ for mapping based quantitation (see :doc:`pipeline_hisat.py <pipelines/pipeline_hisat>` and :doc:`pipeline_feature_counts <pipelines/pipeline_feature_counts>` for more details).

3. Post-mapping QC
------------------

Useful insight can be gained from examining read mapping statistics. Txseq can compute a suite of metrics using the 'CollectRnaSeqMetrics', 'EstimateLibraryComplexity', 'CollectAlignmentSummaryMetrics' and 'CollectInsertSizeMetrics' tools from the `Picard toolkit <https://broadinstitute.github.io/picard/>`_. It also computes the fraction of spliced reads. This functionality is implemented in :doc:`pipeline_bam_qc<pipelines/pipeline_bam_qc>`.

4. Downstream analysis
----------------------

The pipelines generated counts, TPMs and QC statistics for downstream analysis. Examples of how the outputs can be used to assess read quality, perform exploratory analysis and to perform differentially expression analysis are provided as R markdown notebooks for an example dataset. 




