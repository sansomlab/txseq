Configuration Files
===================

Defining samples and sequencing files
-------------------------------------

Txseq requires two tab-seperated files to be provided that specify the sample and sequencing library information. It is not necessary to rename or merge FASTQ files before running txseq: the pipelines will automatically combine sequence data for the same samples and label outputs by the given "sample_id".


(1) "samples.tsv"
^^^^^^^^^^^^^^^^^

A tab-separated text file with the following mandatory columns:

* "sample_id": a unique identifier for the sample
* "type": either 'SE' for single end or 'PE' for paired end
* "strand": either 'none', 'forward' or 'reverse' (see note below).

Sample metadata can also be stored in this table for downstream analysis for 
example with columns such as:

* "condition"
* "replicate"
* "age"
* "sex"
* "genotype"
* "batch"

.. note:: strand values of 'none', 'forward' and 'reverse' will be used to set parameter values in txseq pipelines as follows:

  * "none":  data is treated as unstranded. This is appropriate for e.g. Illumina Truseq and most single-cell protocols. :

    * hisat: default, i.e. --rna-strandedness not set
    * cufflinks: fr-secondstrand
    * HT-seq: no
    * PICARD: NONE
    * SALMON: (I)U

  * "forward": The first read (if paired) or read (if single end) corresponds to the transcript strand e.g. Directional Illumina, Standard Solid.

    * hisat: SE: F, PE: FR
    * cufflinks: fr-secondstrand
    * HT-seq: yes
    * PICARD: FIRST_READ_TRANSCRIPTION_STRAND
    * SALMON: (I)SF
    
  * "reverse": The first read (if paired) or read (if single end) corresponds to the reverse complement of the  transcript strand e.g. dUTP, NSR, NNSR

    * hisat: SE: R, PE: RF
    * cufflinks: fr-firststrand
    * HT-seq: reverse
    * PICARD: SECOND_READ_TRANSCRIPTION_STRAND
    * SALMON: (I)SR

An example samples.tsv file is shown below:

.. literalinclude:: ../examples/mouse_hscs/samples.tsv
    :language: Bash


(2) "libraries.tsv" (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Required when starting from FASTQ files.

A tab-separated text file with the following mandatory columns

* "sample_id": these values must match those in the sample_id in the samples.tsv
* "lane": an integer representing the sequencing lane/unit. 
* "flow_cell": an integer representing the flow cell.
* "fastq_path": For SE libraries, the fastq file path. For PE libraries: the 
   read 1 fastq: the path for read 2 is imputed by the pipelines.

.. Note:: 
    When samples have been sequenced across multiple lanes, use one line per lane. Comma-separated lane and fastq_path values are not supported. Quality control analysis is performed at lane level; lanes will be aggregated for quantitation.

.. Note:: 
    Paired-end fastq files must end with "1|2.fastq.gz" or "fastq.1|2.gz". For paired end samples the Read 1 and Read 2 FASTQ files for the same lane must be located in the same folder.

An example libraries.tsv file is shown below:

.. literalinclude:: ../examples/mouse_hscs/libraries.tsv
    :language: Bash


Configuring and running pipelines
---------------------------------

Run the txseq --help command to view the help documentation and find available pipelines to run.

The txseq pipelines are written using `cgat-core <https://github.com/cgat-developers/cgat-core>`_ pipelining system. From more information please see the `CGAT-core paper <https://doi.org/10.12688/f1000research.18674.2>`_. Here we illustrate how the pipelines can be run using the cellranger pipeline as an example.

Following installation, to find the available pipelines run: ::

  txseq -h

Next generate a configuration yml file: ::

  txseq salmon config -v5

To fully run e.g. the txseq salmon pipeline the following command is used: ::

  txseq salmon make full -v5 -p20
  
The "-v5" flag sets the verbosity level to the maximum level and the "-p20" flag tells the pipeline to launch upto 20 jobs in parallel: this number should be set according to the sample number and availability of compute resources.

It is also possible to run individual pipeline tasks to get a feel of what each one is doing. Individual tasks can then be executed by name, e.g. ::

  txseq salmon make quant -v5 -p20

.. note:: If any upstream tasks are out of date they will automatically be run before the named task is executed.


Getting Started
---------------

To get started please see the :doc:`Mouse hscs example <mouse_hscs_example>`. 

