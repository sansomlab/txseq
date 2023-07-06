'''
samples.py
==========

Overview
--------

This module contains a class that is used to model sample properties and attributes.

Usage
-----

Instantiating a sample
^^^^^^^^^^^^^^^^^^^^^^

Class and method documentation
------------------------------

'''

import yaml
import os
import shutil
import re
import copy
import pandas as pd
from pprint import pprint

# ------------------------------ utility functions -------------------------------- #

def check_cols(pd_frame, req_columns_list,
               table_name="default"):

    for col_name in req_columns_list:
        if col_name not in pd_frame.columns:
            raise ValueError("required column: '" + col_name + "' missing "
                             "in " + table_name + " table")


def check_values(pd_frame, col, allowed):
    '''utility function for sanity checking columns'''
    if not all([x in allowed for x in pd_frame[col].values]):
        raise ValueError("Only the following values are allowed in column '"
                         + col + "': " + ",".join(allowed))

# ------------------------------------ classes --------------------------------------- #

class sample():
    '''
    A class for modelling samples.
    '''

    def __init__(self, attributes):

        mandatory_attributes = ["type", "strand","fastq"]
        
        for x in mandatory_attributes:
            if x not in attributes.keys():
                raise ValueError("Required '" + x + "' sample attribute missing")

        for key in attributes:
            setattr(self, key, attributes[key])
            
        # Determine library type and check fastqs exist
        if self.type.lower() == "pe":
            self.paired = True
            if "read1" not in self.fastq.keys():
                raise ValueError("Required 'read1' path attribute is missing")
            if "read2" not in self.fastq.keys():
                raise ValueError("Required 'read2' path attribute is missing")
                
                    # Check source files exist
            fq_count=0
            
            for x in [x.strip() for x in self.fastq["read1"]]:
                fq_count += 1 
                if not os.path.exists(x):
                    raise ValueError("Read 1 file : " + x + " does not "
                                        "exist")

            for x in [x.strip() for x in self.fastq["read2"]]:
                fq_count -= 1
                if not os.path.exists(x):
                    raise ValueError("Read 2 file : " + x + " does not "
                                        "exist")
            
            if fq_count != 0 :
                raise ValueError("A different number of Read 1 and Read 2 files "
                             "were specified")
            
        elif self.type.lower() == "se":
            self.paired = False
            
            for x in [x.strip() for x in self.fastq]:
                if not os.path.exists(x):
                    raise ValueError("Fastq file : " + x + " does not "
                                        "exist")
        
        else:
            raise ValueError("library type not recognised: should be "
                             "either 'SE' or 'PE'")

        # set options based on strandedness
        self.strand = str(self.strand.lower())
        
        
        
        if self.strand not in ("none", "forward", "reverse"):
            raise ValueError("Strand not recognised")

        if self.strand == "none":
            self.cufflinks_strand = "fr-unstranded"
            self.featurecounts_strand = "0"
            self.picard_strand = "NONE"
            self.salmon_strand = "U"

        elif self.strand == "forward":
            if self.paired:
                self.hisat_strand = "FR"
            else:
                self.hisat_strand = "F"
            self.salmon_strand = "SF"
            self.cufflinks_strand = "fr-secondstrand"
            self.featurecounts_strand = "1"
            self.picard_strand = "FIRST_READ_TRANSCRIPTION_STRAND"

        elif self.strand == "reverse":
            if self.paired:
                self.hisat_strand = "RF"
            else:
                self.hisat_strand = "R"
            self.salmon_strand = "SR"
            self.cufflinks_strand = "fr-firststrand"
            self.featurecounts_strand = "2"
            self.picard_strand = "SECOND_READ_TRANSCRIPTION_STRAND"

        if self.paired:
            self.salmon_libtype = "I" + self.almon_strand
        else:
            self.salmon_libtype = self.salmon_strand

        # self.spikes = self.spikein_present 
            

    def show(self):
        '''
        Print the api object for debugging.
        '''

        pprint(vars(self))


class samples():
    '''
    A class for modelling a set of samples and their associated
    FASTQ files
    '''

    def __init__(self, 
                 sample_tsv, 
                 library_tsv):
    
        # Parse and sanity check the sample table
        
        sample_table = pd.read_csv(sample_tsv, sep="\t")
        
        if not sample_table["sample_id"].is_unique:
            raise ValueError("Non-unique sample_ids provided")
        
        st_req_cols = ["sample_id","type","strand"]
        
        check_cols(sample_table, st_req_cols, "samples.tsv")
        
        st_req_vals = {"type":["SE","PE"],
                       "strand":["none","forward","reverse"]}
        
        for col in st_req_vals.keys():
            check_values(sample_table, col, st_req_vals[col])
    
        sample_table.index = sample_table["sample_id"]
        
        samples = sample_table.to_dict(orient='index')
        
        # Parse and sanity check the library_table
        
        library_table = pd.read_csv(library_tsv, sep="\t")
        
        lt_req_cols = ["sample_id","lane","flow_cell","fastq_path"]
        
        check_cols(library_table, lt_req_cols, "libraries.tsv")
        
        library_table["seq_id"] = library_table[["sample_id","lane","flow_cell"
                                                 ]].astype(str).T.apply(
                                                lambda c: c.str.cat(sep='_'))
        
        libs = library_table.to_dict(orient='index')        
        fastqs = {}
        
        for idx, entry in libs.items():
        
            fqp = libs[idx]["fastq_path"]
            sid = libs[idx]["sample_id"]
            
            paired = True if samples[sid]["type"] == "PE" else False    
            
            if not os.path.exists(fqp):
                raise ValueError("fastq_path for sample '" + sid +"' does not "
                                 "exist: " + fqp)
                              
            if paired:
            
                if fqp.endswith("1.fastq.gz"):
                    r2p = fqp.replace("1.fastq.gz","2.fastq.gz")
                elif fqp.endswith("1.fq.gz"):
                    r2p = fqp.replace("1.fq.gz","2.fq.gz")
                elif fqp.endswith("fastq.1.gz") or fqp.endswith("fq.1.gz"):
                    r2p = fqp.replace("1.gz", "2.gz")
                else:
                    raise ValueError("Read 1 FASTQ file end suffix not recognised. "
                                     "The following suffixes are supported: " 
                                     "1.fastq.gz, 1.fq.gz, fastq.1.gz, fq.1.gz")
                
                if not "fastqs" in samples[sid].keys():
                    samples[sid]["fastq"]={"read1": [fqp], "read2": [r2p]}
                else:
                    samples[sid]["fastq"]["read1"].append(fqp)
                    samples[sid]["fastq"]["read2"].append(r2p)
                    
                fastqs[libs[idx]["seq_id"] + "_R1"] = fqp
                fastqs[libs[idx]["seq_id"] + "_R2"] = r2p
            
            else:
                if not "fastqs" in samples[sid].keys():
                    samples[sid]["fastq"] = [fqp]
                else:
                    samples[sid]["fastq"].append(fqp)
                
                fastqs[libs[idx]["seq_id"]] = fqp
        
        
        self.samples = {}
        for sid, attrs in samples.items():
            self.samples[sid] = sample(attrs)
        
        self.sample_table = sample_table
        self.library_table = library_table
        self.libs = libs
        self.fastqs = fastqs


