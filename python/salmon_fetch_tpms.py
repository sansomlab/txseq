import os
import re
import argparse
import logging
import sys
import sqlite3
import pandas as pd
import numpy as np


# <------------------------------ Logging ------------------------------------>

L = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
log_handler.setLevel(logging.INFO)
L.addHandler(log_handler)
L.setLevel(logging.INFO)

# <------------------------------ Arguments ---------------------------------->

L.info("parsing arguments")

parser = argparse.ArgumentParser()
parser.add_argument("--database", default="csvdb", type=str,
                    help=("The path to the sqlite database"))
parser.add_argument("--table", default=None, type=str,
                    help=("The table name"))
parser.add_argument("--idname", default="gene_id", type=str,
                    help='the name of the column containing the gene '
                         'or transcript identifiers')
parser.add_argument("--outfile", default=None, type=str,
                    help=("name of the gzip compressed outfile"))

args = parser.parse_args()

L.info("Running with arguments:")
print(args)

# <--------------------------- Sanity checks(s) ------------------------------>

if not os.path.exists(args.database):
    raise ValueError("Database file: " + args.ensemblgtf + " does not exist")
    
    
# <--------------------------- fetch the TPMs ------------------------------>


L.info("fetching the data from the database")

con = sqlite3.connect(args.database)

c = con.cursor()

sql = '''select sample_id, Name %(idname)s, TPM tpm
            from %(table)s
        ''' % vars(args)

df = pd.read_sql(sql, con)

L.info("pivoting to a wide table")
#df = df.pivot(index=args.idname, columns=["sample_id", "tpm"])
# df.pivot uses too much memory.
#df.to_csv(args.outfile, sep="\t", index=True, index_label=id_name)

out_df = pd.DataFrame(index=[x for x in df[args.idname].unique()])
#out_df[args.idname] = out_df.index

for sample in [x for x in df["sample_id"].unique()]:

    sample_df = df[df["sample_id"]==sample].copy()
    sample_df.index = sample_df[args.idname]
    
    out_df[sample] = np.NaN
    out_df.loc[sample_df.index, sample] = sample_df["tpm"]


out_df.to_csv(args.outfile, sep="\t", index=True, index_label=args.idname)

L.info("complete")