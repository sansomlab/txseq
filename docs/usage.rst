Usage
=====


Configuring and running pipelines
---------------------------------

Run the txseq --help command to view the help documentation and find available pipelines to run.

The txseq pipelines are written using `cgat-core <https://github.com/cgat-developers/cgat-core>`_ pipelining system. From more information please see the `CGAT-core paper <https://doi.org/10.12688/f1000research.18674.2>`_. Here we illustrate how the pipelines can be run using the cellranger pipeline as an example.

Following installation, to find the available pipelines run: ::

  txseq -h

Next generate a configuration yml file: ::

  txseq salmon config -v5

To fully run e.g. the txseq salmon pipeline the following command is used: ::

  txseq salmon make full -v5 -p20
  
The "-v5" flag sets the verbosity level to the maximum level and the "-p20" flag tells the pipeline to launch upto 20 jobs in parallel: this number should be set according to the sample number and availability of compute resources.

It is also possible to run individual pipeline tasks to get a feel of what each one is doing. Individual tasks can then be executed by name, e.g. ::

  txseq salmon make quant -v5 -p20

.. note:: If any upstream tasks are out of date they will automatically be run before the named task is executed.


Getting Started
---------------

To get started please see the :doc:`Mouse hscs example <mouse_hscs_example>`. 

