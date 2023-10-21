import os
import re
import argparse
import logging
import sys
import gzip
from Bio import SeqIO
from Bio.Align import bed

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
parser.add_argument("--contigs", default="contigs", type=str,
                    help='A text file with the contig names, one per line')
parser.add_argument("--mask", default=None, type=str,
                    help=("A bed file containing genomic intervals"
                          " from which transcripts are to be excluded"))
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
    
if not os.path.exists(args.contigs) or args.contigs is None:
    raise ValueError("Contigs file not specified or missing")

if not os.path.exists(args.mask) or args.mask is None:
    raise ValueError("Mask file not specified or missing")

# <--------------------------- Filter the GTF ------------------------------>


L.info("reading in list of contigs to be included")
contigs = []

with open(args.contigs,"r") as cf:

    for line in cf:
        if line != "":
            contigs.append(line.strip())

L.info("reading in regions to mask")
masks = {}
with open(args.mask) as mf:

    intervals = bed.AlignmentIterator(mf)
    
    for interval in intervals:
    
        name = interval.target.id
        start = interval.coordinates[0][0]
        end = interval.coordinates[0][1]
        
        if name not in masks.keys():
            masks[name] = []
        
        masks[name].append([min([start,end]),max([start,end])])

# GTF file format
# contig    source    type  start   end ....


L.info("filtering ensembl GTF records")
with gzip.open(args.outfile, "wt") as out_file:

    skipped_contigs = {}
    skipped_genes = {}
    n_masked_entries_filtered = 0

    L.info(">>>>> processing file: " + args.ensemblgtf)

    gtf_handle = gzip.open(args.ensemblgtf,"rt")

    for record in gtf_handle:
        
        if record.startswith("#"):
            continue
        
        fields = record.split("\t")
        contig = fields[0]
        start = int(fields[3])
        end = int(fields[4])
                
        x = min([start, end])
        y = max([start, end])
        
                    
        if contig not in contigs:
        
            if contig not in skipped_contigs.keys():
                skipped_contigs[contig] = 1
            else:
                skipped_contigs[contig] += 1

            continue
        
        in_masked = False    
        
        
        if contig in masks.keys():
        
            contig_masks = masks[contig]
            
        
            for masked_region in contig_masks:
        
                #print(masked_region)
                if x > masked_region[0] and y < masked_region[1]:
     
                    # extract the gene_id for logging purposes
                    gtfattrs = [x.strip() for x in fields[8].replace("; ",";").split(";")]
                    for gtfattr in gtfattrs:
                        if gtfattr != "":
                            attr_bits = gtfattr.strip().split(" ")
                            key, value = gtfattr.strip().split(" ")
                            if key == "gene_id":
                                gene = value
                                break
                    
                    if contig not in skipped_genes.keys():
                        skipped_genes[contig] = {"genes": [gene]}
                    else:
                        if gene not in skipped_genes[contig]["genes"]:
                            skipped_genes[contig]["genes"].append(gene)
                                
                    in_masked = True
                    n_masked_entries_filtered += 1
                    break
        
        if in_masked == False:            
            out_file.write("%s" % (record))
            
    L.info("Summary of excluded contig filtering:")
    for contig,count in skipped_contigs.items():
        print("Filtered out " + str(count) + " entries on excluded contig " + contig)

    L.info("Summary of filtering of genes in masked regions on included contigs:")
    for contig,record in skipped_genes.items():
        print("Filtered out " + str(n_masked_entries_filtered) + " entries from " 
              + str(len(record["genes"])) + 
              " genes in masked region(s) on included contig " + contig)
        print("The filtered genes on contig " + contig + " were: ")
        print(",".join(record["genes"]))
        
    L.info("<<<<< finished processing file: " + args.ensemblgtf)

L.info("completed filtering")

L.info("complete")