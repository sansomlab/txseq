import os
import re
import argparse
import logging
import sys
import gzip
import copy

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
parser.add_argument("--ensemblgtf", default=None, type=str,
                    help=("Ensembl GTF file"
                          "An Ensembl GTF file"))
parser.add_argument("--attributes", default="contigs", type=str,
                    help='A comma separated list of the fields to extract')
parser.add_argument("--outfile", default=None, type=str,
                    help=("name of the gzip compressed outfile"))

args = parser.parse_args()

L.info("Running with arguments:")
print(args)

# <--------------------------- Sanity checks(s) ------------------------------>

if args.ensemblgtf is None:
    raise ValueError("Input GTF file path not given")

if not os.path.exists(args.ensemblgtf):
    raise ValueError("GTF file: " + args.ensemblgtf + " does not exist")

# <--------------------------- Filter the GTF ------------------------------>


# GTF file format
# contig    source    type  start   end ....

take = [x.strip() for x in args.attributes.strip().split(",")]
L.info("extracting the following fields:")
print(take)

# use a template to allow for missing values.
attrs_template = {}
for fname in take:
    attrs_template[fname] = 'NA'

L.info("filtering ensembl GTF records")
with gzip.open(args.outfile, "wt") as out_file:

    out_file.write("\t".join(take)+'\n')

    L.info(">>>>> processing file: " + args.ensemblgtf)

    gtf_handle = gzip.open(args.ensemblgtf,"rt")

    for record in gtf_handle:
        
        if record.startswith("#"):
            continue
        
        fields = record.split("\t")
        
        # only process the transcript records
        if fields[2] != "transcript":
            continue

        attrs = copy.deepcopy(attrs_template)

        # extract the gene_id for logging purposes
        # key-value pairs are delimited by "; " in ensembl GTF files
        gtfattrs = [x.strip() for x in fields[8].replace("; ",";").split(";")]
        for gtfattr in gtfattrs:
            if gtfattr != "":
                # keys and values are seperated by ' ' in ensembl files.
                # note that values can have whitespace so we only split on the
                # first whitespace character.
                attr_bits = gtfattr.strip().split(" ", 1)
                key, value = [x.strip("\'\"") for x in attr_bits]
                attrs[key] = value
                
        out = [attrs[x] for x in take]
        out_file.write("\t".join(out) + "\n")
            
   
        
    L.info("<<<<< finished processing file: " + args.ensemblgtf)


L.info("complete")