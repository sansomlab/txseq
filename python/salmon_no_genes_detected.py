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

    
# <--------------------------- Calculate QC stats ----------------------------->

L.info("fetching the data from the database")

con = sqlite3.connect(args.database)

c = con.cursor()

statement = '''select distinct s.*, i.gene_biotype
                from %(table)s s
                inner join transcript_info i
                on s.gene_id=i.gene_id
            ''' % vars(args)

df = pd.read_sql(statement, con)

L.info("Calculating no. genes per sample")
melted_df = pd.melt(df, id_vars=["gene_id", "gene_biotype"])

grouped_df = melted_df.groupby(["gene_biotype", "variable"])

agg_df = grouped_df.agg({"value": lambda x:
                            np.sum([1 for y in x if y > 0])})

agg_df.reset_index(inplace=True)

count_df = pd.pivot_table(agg_df, index="variable",
                            values="value", columns="gene_biotype")

count_df["total"] = count_df.apply(np.sum, 1)
count_df["sample_id"] = count_df.index

L.info("Saving the result")
count_df.to_csv(args.outfile, index=False, sep="\t")

L.info("complete")