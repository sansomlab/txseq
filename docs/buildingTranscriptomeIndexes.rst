Building transcriptome indexes
==============================

Introduction
------------

Txseq uses `Hisat2 <http://daehwankimlab.github.io/hisat2/>`_ for alignment-based gene expression quantification and `Salmon <https://github.com/COMBINE-lab/salmon>`_ for quasi-alignment based gene expression quantification. To use these tools, it is first necessary to build method-specific transcriptomes indexes. 

As with preparation of the sanitised genome sequences and gene annotations, it is recommended to build transcriptome indexes in a central location for use in multiple projects.

Txseq has dedicated pipelines for building Salmon and Hisat2 indexes which can be used as follows.

.. note:: If you are using the KIR BMRC workspace, Salmon and Hisat index built with txseq can be found in the "/well/kir/projects/mirror/txseq/" directory.

Building a Salmon Index
-----------------------

In a suitably named directory, obtain the :doc:`pipeline_salmon_index.py <pipelines/pipeline_salmon_index>` configuration file with the following command::

    mkdir salmon.index.dir
    cd salmon.index.dir
    txseq salmon_index config
    emacs pipeline_salmon_index.yml

After editing the yaml to point to the location of the "txseq.genome.fa.gz" and "txseq.transcript.fa.gz" files (see the "Genomes and Annotations" section), and configuring the parameters as desired, the pipeline can be executed with the following command::

    txseq salmon_index make full -v5 -p20


Building a Hisat2 Index
-----------------------

In a suitably named directory, obtain the :doc:`pipeline_hisat_index.py <pipelines/pipeline_hisat_index>` configuration file with the following command::

    mkdir hisat.index.dir
    cd hisat.index.dir
    txseq hisat_index config
    emacs pipeline_hisat_index.yml

After editing the yaml to point to the location of the "txseq.genome.fa.gz" and "txseq.geneset.gtf.gz" files (see the "Genomes and Annotations" section), and configuring the parameters as desired, the pipeline can be executed with the following command::

    txseq hisat_index make full -v5 -p20

