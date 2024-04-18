Installation
============

Dependencies
------------

Core dependencies include:

- Python3
- The cgat-core pipeline framework
- Python packages as per python/requirements.txt
- R >= 4.0
- Various R libraries (see R/install.packages.R)
- The provided txseq R library


Installation
------------

1. Install the cgat-core pipeline system following the instructions here `https://github.com/cgat-developers/cgat-core/ <https://github.com/cgat-developers/cgat-core/>`_.

2. Clone and install the txseq repository e.g.

.. code-block:: Bash
     
     git clone https://github.com/sansomlab/txseq.git
     cd txseq
     python setup.py develop

.. note:: Running "python setup.py develop" is necessary to allow pipelines to be launched via the "txseq" command.

3. In the same virtual or conda environment as cgat-core install the required python packages::

     pip install -r txseq/python/requirements.txt
     
4. Make sure you have the "devtools" and "BiocManager" R libraries pre-installed by running the following command in an R shell:

     install.packages(c("devtools","BiocManager"))

5. Install the required R packages by running the following command from the bash shell::

     Rscript txseq/R/install.packages.R
     
6. Install the txseq R library by running the following command from the bash shell::

     R CMD INSTALL R/txseq


