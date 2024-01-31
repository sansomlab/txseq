"""==================
Pipeline salmon.py
==================

Overview
--------

This pipeline quantifies gene expression from FASTQ files using `Salmon <https://github.com/COMBINE-lab/salmon>`_. 


Configuration
-------------

The pipeline requires a configured :file:`pipeline_salmon.yml` file.

A default configuration file can be generated by executing: ::

   txseq salmon config


Inputs
------

The pipeline requires the following inputs

#. samples.tsv: see :doc:`pipeline_fastqc.py </pipelines/pipeline_fastqc>`
#. libraries.tsv: see :doc:`pipeline_fastqc.py </pipelines/pipeline_fastqc>`
#. txseq annotations: the location where the :doc:`pipeline_ensembl.py </pipelines/pipeline_ensembl>` was run to prepare the annotatations.
#. Salmon index: the location of a salmon index built with :doc:`pipeline_salmon_index.py </pipelines/pipeline_salmon_index>`.


Requirements
------------

The following software is required:

#. Salmon

Output files
------------

The pipeline produces the following outputs:

#. per-sample salmon quantification results in the "salmon.dir" folder
#. a csvdb sqlite database that contains tables of gene and transcript counts and TPMs

.. note::

    It is strongly recommended to parse the raw Salmon results using the `tximport <https://bioconductor.org/packages/release/bioc/html/tximport.html>`_ Bioconductor R package for downstream analysis.
    

Code
====

"""
from ruffus import *

import sys
import shutil
import os
from pathlib import Path
import glob
import sqlite3

import pandas as pd
import numpy as np

from cgatcore import experiment as E
from cgatcore import pipeline as P
from cgatcore import database as DB
import cgatcore.iotools as IOTools


# import local pipeline utility functions
import txseq.tasks as T
import txseq.tasks.samples as samples

# ----------------------- < pipeline configuration > ------------------------ #

# Override function to collect config files
P.control.write_config_files = T.write_config_files

# load options from the yml file
P.parameters.HAVE_INITIALIZED = False
PARAMS = P.get_parameters(T.get_parameter_file(__file__))
PARAMS["txseq_code_dir"] = Path(__file__).parents[1]


if len(sys.argv) > 1:
    if(sys.argv[1] == "make"):
        
        # set the location of the code directory 
        S = samples.samples(sample_tsv = PARAMS["samples"],
                            library_tsv = PARAMS["libraries"])
        
        # Set the database location
        DATABASE = PARAMS["sqlite"]["file"]


# ---------------------- < specific pipeline tasks > ------------------------ #
    
# ---------------------- Salmon TPM calculation ----------------------------- #

def salmon_jobs():

    for sample_id in S.samples.keys():
    
        yield([None,
               os.path.join("salmon.dir",
                            sample_id + ".sentinel"
        )])

@files(salmon_jobs)
def quant(infile, outfile):
    '''
    Per sample quantitation using salmon.
    '''
    
    t = T.setup(infile, outfile, PARAMS,
                memory=PARAMS["salmon_memory"],
                cpu=PARAMS["salmon_threads"])

    sample = S.samples[os.path.basename(outfile)[:-len(".sentinel")]]

    if sample.paired:
        fastq_input = "-1 " + " ".join(sample.fastq["read1"]) +\
                      " -2 " + " ".join(sample.fastq["read2"])

    else:
        fastq_input = "-r " + " ".join(sample.fastq["read1"])

    options = ''
    if not PARAMS['salmon_quant_options'] is None:
        options = PARAMS['salmon_quant_options']
    
    libtype = sample.salmon_libtype
    
    out_path = os.path.join(t.outdir, sample.sample_id)

    tx2gene = os.path.join(PARAMS["txseq_annotations"],"api.dir/txseq.transcript.to.gene.map")

    statement = '''salmon quant -i %(txseq_salmon_index)s
                                -p %(job_threads)s
                                -g %(tx2gene)s
                                %(options)s
                                -l %(libtype)s
                                %(fastq_input)s
                                -o %(out_path)s
                    &> %(log_file)s;
              ''' % dict(PARAMS, **t.var, **locals())
              
    P.run(statement, **t.resources)
    
    IOTools.touch_file(outfile)

@merge(quant, 
       "salmon.dir/salmon.transcripts.sentinel")
def loadSalmonTranscriptQuant(infiles, sentinel):
    '''
    Load the salmon transcript-level results.
    '''

    tables = [x.replace(".sentinel", "/quant.sf") for x in infiles]

    outfile = sentinel.replace(".sentinel",".load")

    P.concatenate_and_load(tables, outfile,
                           regex_filename=".*/(.*)/quant.sf",
                           cat="sample_id",
                           options="-i Name -i sample_id",
                           job_memory=PARAMS["sql_himem"])
    
    IOTools.touch_file(sentinel)


@merge(quant, "salmon.dir/salmon.genes.sentinel")
def loadSalmonGeneQuant(infiles, sentinel):
    '''
    Load the salmon gene-level results.
    '''

    tables = [x.replace(".sentinel", "/quant.genes.sf") for x in infiles]
    outfile = sentinel.replace(".sentinel",".load")

    P.concatenate_and_load(tables, outfile,
                           regex_filename=".*/(.*)/quant.genes.sf",
                           cat="sample_id",
                           options="-i Name -i sample_id",
                           job_memory=PARAMS["sql_himem"])
    
    IOTools.touch_file(sentinel)


@jobs_limit(1)
@transform([loadSalmonTranscriptQuant,
            loadSalmonGeneQuant],
           regex(r"(.*)/(.*).sentinel"),
           r"\1/\2.tpms.txt")
def salmonTPMs(infile, outfile):
    '''
    Prepare a wide table of salmon TPMs (samples x transcripts|genes).
    '''

    table = P.to_table(infile.replace(".sentinel",".load"))

    if "transcript" in table:
        id_name = "transcript_id"
    elif "gene" in table:
        id_name = "gene_id"
    else:
        raise ValueError("Unexpected Salmon table name")

    con = sqlite3.connect(DATABASE)
    c = con.cursor()

    sql = '''select sample_id, Name %(id_name)s, TPM tpm
             from %(table)s
          ''' % locals()

    df = pd.read_sql(sql, con)

    df = df.pivot(index="id_name", columns=["sample_id", "tpm"])
    df.to_csv(outfile, sep="\t", index=True, index_label=id_name)


@jobs_limit(1)
@transform(salmonTPMs,
           suffix(".txt"),
           ".load")
def loadSalmonTPMs(infile, outfile):
    '''
    Load a wide table of salmon TPMs in the project database.
    '''

    if "transcript" in infile:
        id_name = "transcript_id"
    elif "gene" in infile:
        id_name = "gene_id"
    else:
        raise ValueError("Unexpected Salmon table name")

    opts = "-i " + id_name

    P.load(infile, outfile, options=opts,
           job_memory=PARAMS["sql_himem"])





# ---------------------- Copynumber estimation ------------------------------ #

#
# TODO: use of these historical tasks is currently not supported.
#
# Copy number estimation based on spike-in sequences and Salmon TPMs.
# if PARAMS["spikein_estimate_copy_numbers"] is True:
#     run_copy_number_estimation = True
# else:
#     run_copy_number_estimation = False


# @active_if(run_copy_number_estimation)
# @follows(mkdir("copy.number.dir"), loadSalmonTPMs)
# @files("salmon.dir/salmon.genes.tpms.txt",
#        "copy.number.dir/copy_numbers.txt")
# def estimateCopyNumber(infile, outfile):
#     '''
#     Estimate copy numbers based on standard
#     curves constructed from the spike-ins.
#     '''

#     statement = '''Rscript %(scseq_dir)s/R/calculate_copy_number.R
#                    --spikeintable=%(spikein_copy_numbers)s
#                    --spikeidcolumn=gene_id
#                    --spikecopynumbercolumn=copies_per_cell
#                    --exprstable=%(infile)s
#                    --exprsidcolumn=gene_id
#                    --outfile=%(outfile)s
#                 '''
#     P.run(statement)


# @active_if(run_copy_number_estimation)
# @transform(estimateCopyNumber,
#            suffix(".txt"),
#            ".load")
# def loadCopyNumber(infile, outfile):
#     '''
#     Load the copy number estimations to the project database.
#     '''

#     P.load(infile, outfile, options='-i "gene_id"')


# ----------------------- Quantitation target ------------------------------ #

@follows(loadSalmonTPMs) #, loadCopyNumber)
def quantitation():
    '''
    Quantitation target.
    '''
    pass


# ----------------------- load txinfo ------------------------------ #

@files(None,
       "transcript.info.load")
def loadTranscriptInfo(infile, outfile):
    '''
    Load the annotations for salmon into the project database.
    '''

    txinfo = os.path.join(PARAMS["txseq_annotations"],
                          "api.dir/txseq.transcript.info.tsv.gz")
    
    if not os.path.exists(txinfo):
        raise ValueError("txseq annotations transcript information file not found")

    # will use ~15G RAM
    P.load(txinfo, outfile, options='-i "gene_id" -i "transcript_id"')


# ------------------------- No. genes detected ------------------------------ #

@jobs_limit(1)
@follows(mkdir("qc.dir/"), loadSalmonTPMs, loadTranscriptInfo)
@files("salmon.dir/salmon.genes.tpms.load",
       "qc.dir/number.genes.detected.salmon")
def numberGenesDetectedSalmon(infile, outfile):
    '''
    Count no genes detected at copynumer > 0 in each sample.
    '''

    table = P.to_table(infile)

    statement = '''select distinct s.*, i.gene_biotype
                   from %(table)s s
                   inner join transcript_info i
                   on s.gene_id=i.gene_id
                ''' % locals()

    df = DB.fetch_DataFrame(statement, DATABASE)

    melted_df = pd.melt(df, id_vars=["gene_id", "gene_biotype"])

    grouped_df = melted_df.groupby(["gene_biotype", "variable"])

    agg_df = grouped_df.agg({"value": lambda x:
                             np.sum([1 for y in x if y > 0])})
    agg_df.reset_index(inplace=True)

    count_df = pd.pivot_table(agg_df, index="variable",
                              values="value", columns="gene_biotype")
    count_df["total"] = count_df.apply(np.sum, 1)
    count_df["sample_id"] = count_df.index

    count_df.to_csv(outfile, index=False, sep="\t")


@jobs_limit(1)
@files(numberGenesDetectedSalmon,
       "qc.dir/qc_no_genes_salmon.load")
def loadNumberGenesDetectedSalmon(infile, outfile):
    '''
    Load the numbers of genes expressed to the project database.
    '''

    P.load(infile, outfile,
           options='-i "sample_id"')


# --------------------- < generic pipeline tasks > -------------------------- #

@follows(quantitation, loadNumberGenesDetectedSalmon)
def full():
    pass


def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)

if __name__ == "__main__":
    sys.exit(P.main(sys.argv))
