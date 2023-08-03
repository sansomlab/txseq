"""==============
Pipeline bam_qc
===============

Overview
========

This pipeline computes QC statistic from BAM files. It uses the `Picard toolkit <https://broadinstitute.github.io/picard/>`_ and some custom scripts.


Usage
=====

See :ref:`PipelineSettingUp` and :ref:`PipelineRunning` on general
information how to use CGAT pipelines.

Configuration
-------------

The pipeline requires a configured :file:`pipeline_bam_qc.yml` file.

Default configuration files can be generated by executing:

   python <srcdir>/pipeline_bam_qc.py config


Inputs
------

1. BAM files
^^^^^^^^^^^^^

The pipeline runs against BAM files present in the "api/bam" directory.


Requirements
------------

On top of the default CGAT setup, the pipeline requires the following
software to be in the path:

Requirements:

* Picard

Pipeline output
===============

.. TBC

Glossary
========

.. glossary::


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

# set the location of the code directory
PARAMS["txseq_code_dir"] = Path(__file__).parents[1]

PAIRED = False

if len(sys.argv) > 1:
    if(sys.argv[1] == "make"):
        S = samples.samples(sample_tsv = PARAMS["sample_table"],
                            library_tsv = None)

        if S.npaired > 0: PAIRED = True


# ---------------------- < specific pipeline tasks > ------------------------ #

# ------------------------- Geneset Definition ------------------------------ #

@follows(mkdir("annotations.dir"))
@files(PARAMS["geneset"],
       "annotations.dir/geneset.flat.sentinel")
def flatGeneset(infile, sentinel):
    '''
    Prepare a flat version of the geneset
    for the Picard CollectRnaSeqMetrics module.
    '''

    t = T.setup(infile, sentinel, PARAMS,
            memory="4G",
            cpu=1)

    outfile = sentinel.replace(".sentinel", ".gz")

    statement = '''gtfToGenePred
                    -genePredExt
                    -geneNameAsName2
                    -ignoreGroupsWithoutExons
                    %(infile)s
                    /dev/stdout |
                    awk 'BEGIN { OFS="\\t"}
                         {print $12, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10}'
                    | gzip -c
                    > %(outfile)s
                 '''

    P.run(statement)
    IOTools.touch_file(sentinel)


# ------------------- Picard: CollectRnaSeqMetrics -------------------------- #


def collect_rna_seq_metrics_jobs():

    for sample_id in S.samples.keys():
    
        yield([os.path.join("api", "bam", sample_id + ".bam"),
                os.path.join("bam.qc.dir/rnaseq.metrics.dir/",
                            sample_id + ".rnaseq.metrics.sentinel")])

@follows(flatGeneset)
@files(collect_rna_seq_metrics_jobs)
def collectRnaSeqMetrics(infile, sentinel):
    '''
    Run Picard CollectRnaSeqMetrics on the bam files.
    '''

    t = T.setup(infile], sentinel, PARAMS,
            memory=PARAMS["picard_memory"],
            cpu=PARAMS["picard_threads"])

    bam_file = infile
    geneset_flat = "annotations.dir/geneset.flat.gz"
    
    sample_id = os.path.basename(bam_file)[:-len(".bam")]
    sample = S.samples[sample_id]
    picard_strand = sample.picard_strand

    if PARAMS["picard_collectrnaseqmetrics_options"]:
        picard_options = PARAMS["picard_collectrnaseqmetrics_options"]
    else:
        picard_options = ""

    validation_stringency = PARAMS["picard_validation_stringency"]

    coverage_out = t.out_file[:-len(".metrics")] + ".cov.hist"
    chart_out = t.out_file[:-len(".metrics")] + ".cov.pdf"


    statement = '''picard_out=`mktemp -p tmp.dir`;
                   %(picard_cmd)s CollectRnaSeqMetrics
                   -I %(bam_file)s
                   -REF_FLAT %(geneset_flat)s
                   -O $picard_out
                   -CHART %(chart_out)s
                   -STRAND_SPECIFICITY %(picard_strand)s
                   -VALIDATION_STRINGENCY %(validation_stringency)s
                   %(picard_options)s;
                   grep . $picard_out | grep -v "#" | head -n2
                   > %(out_file)s;
                   grep . $picard_out
                   | grep -A 102 "## HISTOGRAM"
                   | grep -v "##"
                   > %(coverage_out)s;
                   rm $picard_out;
                ''' % dict(PARAMS, **t.var, **locals())

    P.run(statement)
    IOTools.touch_file(sentinel)


@merge(collectRnaSeqMetrics,
       "qc.dir/qc_rnaseq_metrics.load")
def loadCollectRnaSeqMetrics(infiles, outfile):
    '''
    Load the metrics to the db.
    '''
    
    infiles = [x.replace(".sentinel", "") for x in infiles]

    P.concatenate_and_load(infiles, outfile,
                           regex_filename=".*/.*/(.*).rnaseq.metrics",
                           cat="sample_id",
                           options='-i "sample_id"')


# --------------------- Three prime bias analysis --------------------------- #

@transform(collectRnaSeqMetrics,
           suffix(".rnaseq.metrics.sentinel"),
           ".three.prime.bias")
def threePrimeBias(infile, outfile):
    '''
    Compute a sensible three prime bias metric
    from the picard coverage histogram.
    '''

    infile = infile.replace(".sentinel", "")

    coverage_histogram = infile[:-len(".metrics")] + ".cov.hist"

    df = pd.read_csv(coverage_histogram, sep="\t")

    x = "normalized_position"
    cov = "All_Reads.normalized_coverage"

    three_prime_coverage = np.mean(df[cov][(df[x] > 70) & (df[x] < 90)])
    transcript_body_coverage = np.mean(df[cov][(df[x] > 20) & (df[x] < 90)])
    bias = three_prime_coverage / transcript_body_coverage

    with open(outfile, "w") as out_file:
        out_file.write("three_prime_bias\n")
        out_file.write("%.2f\n" % bias)


@merge(threePrimeBias,
       "bam.qc.dir/qc_three_prime_bias.load")
def loadThreePrimeBias(infiles, outfile):
    '''
    Load the metrics in the project database.
    '''

    P.concatenate_and_load(infiles, outfile,
                           regex_filename=".*/.*/(.*).three.prime.bias",
                           cat="sample_id",
                           options='-i "sample_id"')


# ----------------- Picard: EstimateLibraryComplexity ----------------------- #


def estimate_library_complexity_jobs():

    for sample_id in S.samples.keys():
    
        if  S.samples[sample_id].paired == True:
    
            yield([os.path.join("api", "bam", sample_id + ".bam"),
                   os.path.join("bam.qc.dir/estimate.library.complexity.dir/",
                                sample_id + ".library.complexity.sentinel")])

@active_if(PAIRED)
@files(estimate_library_complexity_jobs)
def estimateLibraryComplexity(infile, sentinel):
    '''
    Run Picard EstimateLibraryComplexity on the BAM files.
    '''
    t = T.setup(infile, sentinel, PARAMS,
        memory=PARAMS["picard_memory"],
        cpu=PARAMS["picard_threads"])

    if PARAMS["picard_estimatelibrarycomplexity_options"]:
        picard_options = PARAMS["picard_estimatelibrarycomplexity_options"]
    else:
        picard_options = ""

    validation_stringency = PARAMS["picard_validation_stringency"]

    statement = '''picard_out=`mktemp -p tmp.dir`;
                   %(picard_cmd)s EstimateLibraryComplexity
                   -I %(infile)s
                   -O $picard_out
                   -VALIDATION_STRINGENCY %(validation_stringency)s
                   %(picard_options)s;
                   grep . $picard_out | grep -v "#" | head -n2
                   > %(out_file)s;
                   rm $picard_out;
                ''' % dict(PARAMS, **t.var, **locals())

    P.run(statement)
    IOTools.touch_file(sentinel)
    

@active_if(PAIRED)
@merge(estimateLibraryComplexity,
       "bam.qc.dir/qc_library_complexity.load")
def loadEstimateLibraryComplexity(infiles, outfile):
    '''
    Load the complexity metrics to a single table in the project database.
    '''

    P.concatenate_and_load(infiles, outfile,
                           regex_filename=".*/.*/(.*).library.complexity",
                           cat="sample_id",
                           options='-i "sample_id"')



# ------------------- Picard: AlignmentSummaryMetrics ----------------------- #


def alignment_summary_metrics_jobs():

    for sample_id in S.samples.keys():
    
        yield([os.path.join("api", "bam", sample_id + ".bam"),
                os.path.join("bam.qc.dir/alignment.summary.metrics.dir/",
                            sample_id + ".alignment.summary.metrics.sentinel")])

@files(alignment_summary_metrics_jobs)
def alignmentSummaryMetrics(infile, sentinel):
    '''
    Run Picard AlignmentSummaryMetrics on the bam files.
    '''

    t = T.setup(infiles[0], sentinel, PARAMS,
            memory=PARAMS["picard_memory"],
            cpu=PARAMS["picard_threads"])

    picard_options = PARAMS["picard_alignmentsummarymetric_options"]
    validation_stringency = PARAMS["picard_validation_stringency"]

    reference_sequence = os.path.join(PARAMS["primary_assembly"])

    statement = '''picard_out=`mktemp -p tmp.dir`;
                   %(picard_cmd)s CollectAlignmentSummaryMetrics
                   -I %(infile)s
                   -O $picard_out
                   -REFERENCE_SEQUENCE %(reference_sequence)s
                   -VALIDATION_STRINGENCY %(validation_stringency)s
                   %(picard_options)s;
                   grep . $picard_out | grep -v "#"
                   > %(out_file)s;
                   rm $picard_out;
                ''' % dict(PARAMS, **t.var, **locals())

    P.run(statement)
    IOTools.touch_file(sentinel)


@merge(alignmentSummaryMetrics,
       "bam.qc.dir/qc_alignment_summary_metrics.load")
def loadAlignmentSummaryMetrics(infiles, outfile):
    '''
    Load the complexity metrics to a single table in the project database.
    '''

    P.concatenate_and_load(
        infiles, outfile,
        regex_filename=".*/.*/(.*).alignment.summary.metrics",
        cat="sample_id",
        options='-i "sample_id"')


# ------------------- Picard: InsertSizeMetrics ----------------------- #

def insert_size_jobs():

    for sample_id in S.samples.keys():
    
        if  S.samples[sample_id].paired == True:
    
            yield([os.path.join("api", "bam", sample_id + ".bam"),
                   [os.path.join("bam.qc.dir/insert.size.metrics.dir/",
                                sample_id + ".insert.size.metrics.summary.sentinel"),
                    os.path.join("bam.qc.dir/insert.size.metrics.dir/",
                                sample_id + ".insert.size.metrics.histogram.sentinel"),
                   ]])

@active_if(PAIRED)
@files(insert_size_jobs)
def insertSizeMetricsAndHistograms(infile, sentinels):
    '''
    Run Picard InsertSizeMetrics on the BAM files to
    collect summary metrics and histograms.'''

    t = T.setup(infile, sentinel, PARAMS,
            memory=PARAMS["picard_memory"],
            cpu=PARAMS["picard_threads"])

    picard_summary, picard_histogram = [ x.replace(".sentinel", "") for x in sentinels ]
    picard_histogram_pdf = picard_histogram + ".pdf"

    if PARAMS["picard_insertsizemetric_options"]:
        picard_options = PARAMS["picard_insertsizemetric_options"]
    else:
        picard_options = ""

    validation_stringency = PARAMS["picard_validation_stringency"]
    reference_sequence = os.path.join(PARAMS["primary_assembly"])

    statement = '''picard_out=`mktemp -p tmp.dir`;
                   %(picard_cmd)s CollectInsertSizeMetrics
                   -I %(infile)s
                   -O $picard_out
                   -HISTOGRAM_FILE %(picard_histogram_pdf)s
                   -VALIDATION_STRINGENCY %(validation_stringency)s
                   -REFERENCE_SEQUENCE %(reference_sequence)s
                   %(picard_options)s;
                   grep "MEDIAN_INSERT_SIZE" -A 1 $picard_out
                   > %(picard_summary)s;
                   sed -e '1,/## HISTOGRAM/d' $picard_out
                   > %(picard_histogram)s;
                   rm $picard_out;
                ''' % dict(PARAMS, **t.var, **locals())

    P.run(statement)
    
    for sentinel in sentinels: 
        IOTools.touch_file(sentinel)

@active_if(PAIRED)
@merge(insertSizeMetricsAndHistograms,
       "bam.qc.dir/qc_insert_size_metrics.load")
def loadInsertSizeMetrics(infiles, outfile):
    '''
    Load the insert size metrics to a single table of the project database.
    '''

    picard_summaries = [x[0] for x in infiles]

    P.concatenate_and_load(picard_summaries, outfile,
                            regex_filename=(".*/.*/(.*)"
                                            ".insert.size.metrics.summary"),
                            cat="sample_id",
                            options='')


@active_if(PAIRED)
@merge(insertSizeMetricsAndHistograms,
       "bam.qc.dir/qc_insert_size_histogram.load")
def loadInsertSizeHistograms(infiles, outfile):
    '''
    Load the histograms to a single table of the project database.
    '''

    picard_histograms = [x[1] for x in infiles]

    P.concatenate_and_load(
        picard_histograms, outfile,
        regex_filename=(".*/.*/(.*)"
                        ".insert.size.metrics.histogram"),
        cat="sample_id",
        options='-i "insert_size" -e')




# --------------------- Fraction of spliced reads --------------------------- #


def fraction_spliced_jobs():

    for sample_id in S.samples.keys():
    
        yield([os.path.join("api", "bam", sample_id + ".bam"),
                os.path.join("bam.qc.dir/fraction.spliced.dir/",
                            sample_id + ".fraction.spliced.sentinel")])

@files(fraction_spliced_jobs)
def fractionSpliced(infile, sentinel):
    '''
    Compute fraction of reads containing a splice junction.
    * paired-endedness is ignored
    * only uniquely mapping reads are considered.
    '''
    
    t = T.setup(infile, sentinel, PARAMS)

    statement = '''echo "fraction_spliced" > %(outfile)s;
                   samtools view %(infile)s
                   | grep NH:i:1
                   | cut -f 6
                   | awk '{if(index($1,"N")==0){us+=1}
                           else{s+=1}}
                          END{print s/(us+s)}'
                   >> %(out_file)s
                 ''' % dict(PARAMS, **t.var, **locals())

    P.run(statement)
    IOTools.touch_file(sentinel)


@merge(fractionReadsSpliced,
       "bam.qc.dir/qc_fraction_spliced.load")
def loadFractionReadsSpliced(infiles, outfile):
    '''
    Load fractions of spliced reads to a single table of the project database.
    '''

    P.concatenate_and_load(infiles, outfile,
                           regex_filename=".*/.*/(.*).fraction.spliced",
                           cat="sample_id",
                           options='-i "sample_id"')


# ---------------- Prepare a post-mapping QC summary ------------------------ #


@transform(PARAMS["sample_table"],
           suffix(".tsv"),
           ".load")
def loadSampleInformation(infile, outfile):
    '''
    Load the sample information table to the project database.
    '''

    P.load(infile, outfile)


@merge([loadSampleInformation,
        loadCollectRnaSeqMetrics,
        loadThreePrimeBias,
        loadEstimateLibraryComplexity,
        #loadSpikeVsGenome,
        loadFractionReadsSpliced,
        #loadNumberGenesDetectedSalmon,
        #loadNumberGenesDetectedFeatureCounts,
        loadAlignmentSummaryMetrics,
        loadInsertSizeMetrics],
       "qc.dir/qc_summary.txt")
def qcSummary(infiles, outfile):
    '''
    Create a summary table of relevant QC metrics.
    '''

    # Some QC metrics are specific to paired end data
    if PAIRED:
        exclude = []
        paired_columns = '''READ_PAIRS_EXAMINED as no_pairs,
                              PERCENT_DUPLICATION as pct_duplication,
                              ESTIMATED_LIBRARY_SIZE as library_size,
                              PCT_READS_ALIGNED_IN_PAIRS
                                       as pct_reads_aligned_in_pairs,
                              MEDIAN_INSERT_SIZE
                                       as median_insert_size,
                           '''
        pcat = "PAIR"

    else:
        exclude = ["qc_library_complexity", "qc_insert_size_metrics"]
        paired_columns = ''
        pcat = "UNPAIRED"

    if fastqMode:
        exclude = exclude
        fastq_columns = '''qc_no_genes_salmon.protein_coding
                              as salmon_no_genes_pc,
                           qc_no_genes_salmon.total
                              as salmon_no_genes,
                        '''
    else:
        exclude = exclude + ["qc_no_genes_salmon"]
        fastq_columns = ''

    tables = [P.to_table(x) for x in infiles
              if P.to_table(x) not in exclude]

    t1 = tables[0]

    name_fields = PARAMS["name_field_titles"].strip()

    stat_start = '''select distinct %(name_fields)s,
                                    sample_information.sample_id,
                                    fraction_spliced,
                                    fraction_spike,
                                    %(fastq_columns)s
                                    qc_no_genes_featurecounts.protein_coding
                                       as featurecounts_no_genes_pc,
                                    qc_no_genes_featurecounts.total
                                       as featurecounts_no_genes,
                                    three_prime_bias
                                       as three_prime_bias,
                                    nreads_uniq_map_genome,
                                    nreads_uniq_map_spike,
                                    %(paired_columns)s
                                    PCT_MRNA_BASES
                                       as pct_mrna,
                                    PCT_CODING_BASES
                                       as pct_coding,
                                    PCT_PF_READS_ALIGNED
                                       as pct_reads_aligned,
                                    TOTAL_READS
                                       as total_reads,
                                    PCT_ADAPTER
                                       as pct_adapter,
                                    PF_HQ_ALIGNED_READS*1.0/PF_READS
                                       as pct_pf_reads_aligned_hq
                   from %(t1)s
                ''' % locals()

    join_stat = ""
    for table in tables[1:]:
        join_stat += "left join " + table + "\n"
        join_stat += "on " + t1 + ".sample_id=" + table + ".sample_id\n"

    where_stat = '''where qc_alignment_summary_metrics.CATEGORY="%(pcat)s"
                 ''' % locals()

    statement = "\n".join([stat_start, join_stat, where_stat])

    df = DB.fetch_DataFrame(statement, PARAMS["database_file"])
    df.to_csv(outfile, sep="\t", index=False)


@transform(qcSummary,
           suffix(".txt"),
           ".load")
def loadQCSummary(infile, outfile):
    '''
    Load summary to project database.
    '''

    P.load(infile, outfile)


@follows(loadQCSummary, loadInsertSizeHistograms)
def qc():
    '''
    Target for executing quality control.
    '''
    pass


# --------------------- < generic pipeline tasks > -------------------------- #

@follows(mkdir("notebook.dir"))
@transform(glob.glob(os.path.join(os.path.dirname(__file__),
                                  "pipeline_notebooks",
                                  os.path.basename(__file__)[:-len(".py")],
                                  "*")),
           regex(r".*/(.*)"),
           r"notebook.dir/\1")
def notebooks(infile, outfile):
    '''
    Utility function to copy the notebooks from the source directory
    to the working directory.
    '''

    shutil.copy(infile, outfile)


@follows(qc)
def full():
    pass


print(sys.argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)

if __name__ == "__main__":
    sys.exit(P.main(sys.argv))

