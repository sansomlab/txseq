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
parser.add_argument("--ensembltxfasta", default=None, type=str,
                    help=("Ensembl transcript fasta file(s)"
                          " A single, or a comma seperated list, of gzipped Ensembl FASTA file(s)."))
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

if args.ensembltxfasta is None:
    raise ValueError("Input transcript fasta not given or missing")

ensembl_fasta_files = [x.strip() for x in args.ensembltxfasta.split(",")]

for ensembl_fasta_file in ensembl_fasta_files:
    if not os.path.exists(ensembl_fasta_file):
        raise ValueError("Fasta file: " + ensembl_fasta_file + " does not exist")
    
if not os.path.exists(args.contigs) or args.contigs is None:
    raise ValueError("Contigs file not specified or missing")

if not os.path.exists(args.mask) or args.mask is None:
    raise ValueError("Mask file not specified or missing")

# <--------------------------- Make the loom(s) ------------------------------>



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

# Note from ensembl.org:
#
# ------------------------------
# FASTA Sequence Header Lines
# ------------------------------
# The FASTA sequence header lines are designed to be consistent across
# all types of Ensembl FASTA sequences.

# Stable IDs for genes and transcripts are suffixed with
# a version if they have been generated by Ensembl (this is typical for
# vertebrate species, but not for non-vertebrates).
# All ab initio data is unversioned.

# General format:

# >TRANSCRIPT_ID SEQTYPE LOCATION GENE_ID GENE_BIOTYPE TRANSCRIPT_BIOTYPE

# Example of an Ensembl cDNA header:

# >ENST00000289823.1 cdna chromosome:NCBI35:8:21922367:21927699:1 gene:ENSG00000158815.1 gene_biotype:protein_coding transcript_biotype:protein_coding
#  ^                 ^    ^                                       ^                      ^                           ^
#  TRANSCRIPT_ID     |    LOCATION                                GENE_ID                GENE_BIOTYPE                TRANSCRIPT_BIOTYPE
#                 SEQTYPE




L.info("filtering ensembl FASTA records")
with gzip.open(args.outfile, "wt") as out_file:

    for ensembl_fasta_file in ensembl_fasta_files:

        skipped_contigs = {}
        skipped_genes = {}

        L.info(">>>>> processing file: " + ensembl_fasta_file)

        fasta_sequences = SeqIO.parse(gzip.open(ensembl_fasta_file,"rt"),'fasta')

        for fasta in fasta_sequences:
            
            description, sequence = fasta.description, str(fasta.seq)
            
                        
            #print(fasta.description)
                        
            # Extract the location from the description (see note from ensembl docs above)
            location = description.split(" ")[2].split(":")
                       
            contig = location[2] 
            start = int(location[3])
            end = int(location[4])
            
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
                        
                        gene = description.split(" ")[3].split(":")[1]
                        
                        if contig not in skipped_genes.keys():
                            skipped_genes[contig] = {"genes": [gene],
                                                     "ntx": 1}
                        else:
                            if gene not in skipped_genes[contig]["genes"]:
                                skipped_genes[contig]["genes"].append(gene)
                                
                            skipped_genes[contig]["ntx"] += 1
                        
                        in_masked = True
                        break
            
            # remove the version number from the transcript ID
            # to enable cross-referencing with the ensembl GTF...
            # (.. assume here that multiple versions of the same transcript
            #     will not be present in the GTF)
            out_description = description.split(" ")
            out_name = out_description[0].split(".")[0]
            #out_description = " ".join(out_description)
            #out_name = out_
            
            if in_masked == False:            
                out_file.write(">%s\n%s\n" % (out_name, sequence))
                
        L.info("Summary of excluded contig filtering:")
        for contig,count in skipped_contigs.items():
            print("Filtered out " + str(count) + " genes on excluded contig " + contig)

        L.info("Summary of filtering of genes in masked regions on included contigs:")
        for contig,record in skipped_genes.items():
            print("Filtered out " + str(len(record["genes"])) + " genes and " + str(record["ntx"]) +" transcripts in masked region(s) on included contig " + contig)
            print("The filtered genes on contig " + contig + " were: ")
            print(",".join(record["genes"]))
            
        L.info("<<<<< finished processing file: " + ensembl_fasta_file)

L.info("completed filtering")



L.info("complete")