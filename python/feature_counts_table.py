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
parser.add_argument("--outfile", default=None, type=str,
                    help=("name of the gzip compressed outfile"))

args = parser.parse_args()

L.info("Running with arguments:")
print(args)


# <--------------------------- Sanity checks(s) ------------------------------>

if not os.path.exists(args.database):
    raise ValueError("Database file: " + args.ensemblgtf + " does not exist")

  
# <--------------------------- fetch the counts ------------------------------>

L.info("fetching the data from the database")

con = sqlite3.connect(args.database)

c = con.cursor()

sql = '''select track, gene_id, counts
             from %(table)s t
          ''' % vars(args)

df = pd.read_sql(sql, con)

L.info("pivoting to a wide table")

# df = df.pivot(index="gene_id", columns="track", values="counts")
# df.to_csv(outfile, sep="\t", index=True, index_label="gene_id")


out_df = pd.DataFrame(index=[x for x in df["gene_id"].unique()])

for sample in [x for x in df["track"].unique()]:

    sample_df = df[df["track"]==sample].copy()
    sample_df.index = sample_df["gene_id"]
    
    out_df[sample] = np.NaN
    out_df.loc[sample_df.index, sample] = sample_df["counts"]
    
out_df = out_df.astype(int)

out_df.to_csv(args.outfile, sep="\t", index=True, index_label="gene_id")

L.info("complete")