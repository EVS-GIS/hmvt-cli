# Historical Maps Vectorization Tools

A toolbox to vectorize fluvial corridor objects on historical maps.

![EVS](./img/logo_evs.png) ![OFB](./img/logo-ofb.png)

# Get started with the Command Line Interface environment
## Create a python 3 virtual environment for HMVT
You will need a valid python3 installation.
Create a python3 virtual environment and install the dependencies in requirements.txt : 
    
    python3 -m venv ./env --prompt hmvt
    source ./env/bin/activate
    pip install -r requirements.txt

## Make the hmvt_cli.py file executable

    chmod +x ./hmvt_cli.py

## Use HMVT with CLI
First, activate the virtual environment (the command may be different on a Windows OS) :

    source ./env/bin/activate

Example to process full HMVT on a single tiff file : 

    hmvt_cli.py /path/to/working/directory -i path/to/rgb_map_image.TIF --mask --lab --sample --classif knn --reconstruct

Example to process full HMVT on all the tiff files in the "rgb" folder inside the working directory:

    hmvt_cli.py /path/to/working/directory --mask --lab --sample --classif knn --reconstruct

Example to parallelize processing with hwloc:

* First, use this script to prepare a "run.sh" file

        python prepareParallelProcessing.py -wd /path/to/wd/ --sample --classif knn
    
* Then make the run.sh file executable

        chmod +x ./run.sh

* And execute it:
    
        ./run.sh

