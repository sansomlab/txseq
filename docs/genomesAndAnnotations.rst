Genomes and Annotations
=======================

Introduction
------------

In general, for RNA-seq analysis it is best to use genome sequences and gene annotations that:

#. Include sequences and gene annotations from PRIMARY contigs, i.e. chromosomes, mitochondrial sequences, unlocalised and unplaced scaffolds
#. Do not include sequences and gene annotations from alternative (ALT) contigs
#. Exclude multi-placed transcript sequences by masking/excluding sequence/records from the Y chromosome PAR region. 

The txseq repository uses genome sequences and gene annotations retrieved from `Ensembl <https://www.ensembl.org/index.html>`. These are pre-processed using the "txseq ensembl" command to prepare "txseq-sanitised" versions which address all the issues above.


.. note:: If you are using the KIR BMRC workspace, sanitised genome sequences and gene annotations can be found in the "/well/kir/projects/mirror/txseq/" directory.



Retrieving genome sequences and gene annotations
------------------------------------------------

The following files are required:

#. The Ensembl primary assembly FASTA sequences
#. The Ensembl geneset in GTF format
#. The Ensembl cDNA FASTA sequences
#. The Ensembl ncRNA FASTA sequences 
#. PAR region definitions in BED format

As an example, for the human genome the Ensembl genome and annotation files (for Ensembl release 110) could be retrieved using the following commands::

    wget https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
    wget https://ftp.ensembl.org/pub/release-110/gtf/homo_sapiens/Homo_sapiens.GRCh38.110.gtf.gz
    wget https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/cdna/Homo_sapiens.GRCh38.cdna.all.fa.gz
    wget https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/ncrna/Homo_sapiens.GRCh38.ncrna.fa.gz

The PAR region locations can be retrived from e.g. the `Genome Reference Consortium <https://www.ncbi.nlm.nih.gov/grc/>`, e.g.

#. For `human PAR locations <https://www.ncbi.nlm.nih.gov/grc/human>`
#. For `mouse PAR locations <https://www.ncbi.nlm.nih.gov/grc/mouse>`

The PAR coordinates should be used to prepare a bed file, for example for the GRCh38.p14 release of the human genome the (tab-separated) file should look like this::

    X	10001	2781479	PAR.1
    X	155701383	156030895	PAR.2
    Y	10001	2781479	PAR.1
    Y	56887903	57217415	PAR.2


Preparing a txseq-sanitised genome and annotations
--------------------------------------------------

It is recommended to prepare txseq-sanitised genome sequences and annotations in a central location for use in all of your RNA-seq projects.

In a suitable directory, obtain a copy of the pipeline_ensembl.py configuration file::

    txseq ensembl config
    
After editing the yaml file to provide the locations of the Ensembl genome, Ensembl annotations and the PAR bed file, execute the pipeline with the following command::

    txseq ensembl make full -v5 -p20
    
The output of the pipeline is and "api.dir" folder that contains the following files that can be used to build indexes for RNA-seq mapping and quantification tools:

#. txseq.geneset.gtf.gz - the sanitised geneset
#. txseq.genome.fa.gz - the sanitised and PAR masked genome
#. txseq.transcript.fa.gz - the sanitised transcripts
#. txseq.transcript.info.tsv.gz - a flat tsv table of transcript information (for the santitised transcript set)
#. txseq.transcript.to.gene.map - a flat 2-column tsv table containing a map of transcripts -> genes (for the sanitised transcript set)
