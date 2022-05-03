# -*- coding: utf-8 -*-
"""
***************************************************************************
    prepareParallelProcessing.py
    ---------------------
    Date                 : 2019
    Copyright            : (C) 2019 by Samuel Dunesme
***************************************************************************
*                                                                         *
*                                                                         *
***************************************************************************

__author__ = "Samuel Dunesme"
__date__ = "2019"
__copyright__ = "(C) 2019, Samuel Dunesme"
"""

import os
import glob
import argparse
import multiprocessing


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Generate run.sh for parallel processing of a working directory")

    parser.add_argument("-wd", "--workingdirectory",
                        help="Working directory which contains all the files/folders needed", required=True)
    parser.add_argument("-v", "--valleybottom",
                        help="Valley bottom file to compute masks", default="./valley_bottom/valley_bottom.shp")

    # Etapes de traitement à effectuer
    parser.add_argument(
        "-m", "--mask", help="Create AC masks", action="store_true")
    parser.add_argument(
        "-l", "--lab", help="Convert RGB maps to CIE L*ab", action="store_true")
    parser.add_argument(
        "-s", "--sample", help="Create color sample on the CIE L*lab map", action="store_true")
    parser.add_argument(
        "-c", "--classif", help="Classification method (if classification of map colors wanted)")
    parser.add_argument(
        "-r", "--reconstruct", help="Reconstruction of fluvial corridor's objects", action="store_true")

    # Passage des arguments
    return parser.parse_args()


if __name__ == "__main__":
    # On parse les arguments et on prépare les options choisies
    args = parseArguments()

    additionalArgs = "{}".format(args.workingdirectory)

    if args.valleybottom != None:
        additionalArgs += " -v {}".format(str(args.valleybottom))
    if args.mask:
        additionalArgs += " -m"
    if args.lab:
        additionalArgs += " -l"
    if args.sample:
        additionalArgs += " -s"
    if args.classif != None:
        additionalArgs += " -c {}".format(str(args.classif))
    if args.reconstruct:
        additionalArgs += " -r"

    # On liste les images présentes dans le wd et on les sépare en 2 groupes
    mapList = glob.glob('{}/rgb/*.[tT][iI][fF]'.format(os.path.normpath(args.workingdirectory)))
    nMaps = len(mapList)//2

    group1 = mapList[:nMaps]
    group2 = mapList[nMaps:]

    # On compte les cpu dispo et on les sépare en deux groupes
    cpu_size = int(multiprocessing.cpu_count() / 2)
    cpu1 = "0-{}".format(cpu_size-1)
    cpu2 = "{}-{}".format(cpu_size, (cpu_size*2)-1)

    # On écrit les lignes de commande pour les deux groupes
    group1Command = """\nfor group1 in {flist}
    do
        hwloc-bind -p pu:{cpu} hmvt_cli.py -i $group1 {addargs}
    done &\n""".format(
        cpu=cpu1,
        flist=" ".join(group1),
        addargs=additionalArgs)

    group2Command = """\nfor group2 in {flist}
    do
        hwloc-bind -p pu:{cpu} hmvt_cli.py -i $group2 {addargs}
    done\n""".format(
        cpu=cpu2,
        flist=" ".join(group2),
        addargs=additionalArgs)

    # On met tout ça dans le fichier run.sh
    runFile = open("./run.sh", "w")
    runFile.write("#!/bin/bash\n")
    runFile.write(group1Command)
    runFile.write(group2Command)
    runFile.close()

    print("writing ./run.sh...")