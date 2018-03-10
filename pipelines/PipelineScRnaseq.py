import sys
import os
import re
import sqlite3

import pandas as pd
import numpy as np

import CGAT.Experiment as E
import CGATPipelines.Pipeline as P

import rpy2.robjects as R
from rpy2.robjects import pandas2ri
pandas2ri.activate()


PARAMS = P.getParameters(
    ["%s/pipeline.ini" % os.path.splitext(__file__)[0],
     "../pipeline.ini",
     "pipeline.ini"])


# ########################################################################### #
# ####################### General functions ################################# #
# ########################################################################### #

def runCuffNorm(geneset, cxb_files, labels,
                outdir, logFile,
                library_type="fr-unstranded",
                normalisation="classic-fpkm",
                standards_file=None,
                hits="total"):

    total_mem = PARAMS["cufflinks_cuffnorm_total_mb_memory"]

    job_threads = PARAMS["cufflinks_cuffnorm_threads"]
    job_memory = str(int(total_mem) // int(job_threads)) + "M"

    hits_method = "--%(hits)s-hits-norm" % locals()

    if standards_file:
        norm_standards = "--norm-standards-file=%(standards_file)s" % locals()
    else:
        norm_standards = ""

    statement = ''' gtf=`mktemp -p %(local_tmpdir)s`;
                    checkpoint;
                    zcat %(geneset)s > $gtf;
                    checkpoint;
                    cuffnorm
                        --output-dir %(outdir)s
                        --num-threads=%(job_threads)s
                        --library-type %(library_type)s
                        %(hits_method)s
                        --library-norm-method %(normalisation)s
                        %(norm_standards)s
                        --labels %(labels)s
                        $gtf %(cxb_files)s > %(logFile)s;
                     checkpoint;
                     rm $gtf;
                '''
    P.run()


# ########################################################################### #
# ###################### Copy number functions ############################## #
# ########################################################################### #

def estimateCopyNumber(infiles, outfile, params):
    '''Estimate copy number based on ERCC spike in concentrations.
       Expects the location of the directory containing the
       R code as a single parameter.'''

    infile, cuffnorm_load, ercc_load = infiles
    code_dir = params[0]

    cuffnorm_table = P.toTable(cuffnorm_load)
    ercc_table = P.toTable(ercc_load)

    track = outfile.split("/")[-1][:-len(".spike.norm")]
    plotname = outfile+".png"

    # col_name = track.replace("-","_") + "_0"
    col_name = re.sub(r"[-.]", "_", track) + "_0"

    # ## connect to the database.
    con = sqlite3.connect(PARAMS["database_name"])

    # ## retrieve the spike in data
    statement = '''select e.gene_id, %(col_name)s as FPKM, copies_per_cell
                   from %(ercc_table)s e
                   inner join %(cuffnorm_table)s c
                   on e.gene_id=c.tracking_id
                ''' % locals()

    spikedf = pd.read_sql(statement, con)

    # ## retrieve the data to normalise
    statement = ''' select tracking_id as gene_id, %(col_name)s as FPKM
                    from %(cuffnorm_table)s
                ''' % locals()

    fpkms = pd.read_sql(statement, con)

    script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

    r = R.r

    rscript = os.path.join(os.path.join(code_dir,
                                        PARAMS["rsource"]))

    r.source(rscript)

    plotname, outfile = [os.path.abspath(x) for x in [plotname, outfile]]

    r.normalise_to_spikes(spikedf, fpkms, plotname, outfile, track)
