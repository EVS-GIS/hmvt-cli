#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
***************************************************************************
    main.py
    ---------------------
    Date                 : 2018
    Copyright            : (C) 2018 by Samuel Dunesme
***************************************************************************
*                                                                         *
*                                                                         *
***************************************************************************

__author__ = "Samuel Dunesme"
__date__ = "2018"
__copyright__ = "(C) 2018, Samuel Dunesme"
"""

import sys
import os
import glob
import argparse
import multiprocessing
import psutil
import fiona

from hmvt.classes import MapFiles, CustomLogger


def completeJob(map_object):
    """
    Docstring
    :type map_object: MapFiles
    """

    map_object.logger.resetTimer()

    # ------------------------
    # Création d'un masque de bande active
    if args.mask:
        map_object.logger.stepUpdate("Masking")
        from hmvt.algorithms import masking

        masking.createMaskFile(
            map_object.rgb, map_object.mask, vb_features, map_object.logger
        )

        map_object.logger.message("--done", console=True)

    # ------------------------
    # Conversion L*ab
    if args.lab:
        map_object.logger.stepUpdate("Conversion")
        from hmvt.algorithms import colorimetrie

        colorimetrie.tiledRGB2LAB(map_object.rgb, map_object.lab)

        map_object.logger.message("--done", console=True)

    # ------------------------
    # Échantillonnage
    if args.sample:
        map_object.logger.stepUpdate("Sampling")
        from hmvt.algorithms.learning import samplesFromLAB

        samplesFromLAB(
            map_object.lab,
            map_object.samples,
            map_object.sampleShapes,
            logger=map_object.logger,
        )

        map_object.logger.message("--done", console=True)

    # ------------------------
    # Classification
    if args.classif != None:
        map_object.logger.stepUpdate("Classification")
        map_object.logger.message("classification method :" + str(args.classif))
        from hmvt.algorithms import learning

        # Apprentissage avec OTB
        if args.classif == "knn":
            learning.knnClassification(
                map_object.lab,
                map_object.samples,
                map_object.colorLayers,
                map_object.logger,
                map_object.mask,
            )
        # elif args.classif == "svm":
        #     learning.SVMClassification(
        #         map_object.lab,
        #         map_object.sampleShapes,
        #         map_object.classifModel,
        #         map_object.confMatModel,
        #         map_object.memory,
        #         map_object.logger,
        #     )
        elif args.classif == "rf":
            learning.rfClassification(
                map_object.lab,
                map_object.samples,
                map_object.colorLayers,
                map_object.logger,
            )
        else:
            map_object.logger.message(
                'classification method "{}" unrecognized'.format(str(args.classif)),
                console=True,
            )
            return

        map_object.logger.message("--done", console=True)

    # ------------------------
    # Reconstruction
    if args.reconstruct:
        map_object.logger.stepUpdate("Reconstruction")
        from hmvt.algorithms import reconstruction

        reconstruction.fluvialCorridorReconstruction(
            map_object.colorLayers,
            map_object.lab,
            map_object.objects,
            map_object.polygonalObjects,
            map_object.linearObjects,
            map_object.logger,
        )

        map_object.logger.message("--done", console=True)

    # ------------------------
    # Validation
    map_object.logger.stepUpdate("Validation")
    from hmvt.algorithms import validation

    try:
        # Rapport final
        validation.makeReport(map_object.mask, map_object.name, map_object.logger)

        # Matrices de confusion si il existe des données de validation
        if os.path.isfile(map_object.valiData):
            if os.path.isfile(map_object.colorLayers):
                map_object.logger.message("color layers validation")
                # Matrice de confusion pour les couches de couleurs
                validation.computeConfusionMatrix(
                    map_object.colorLayers,
                    map_object.valiData,
                    map_object.confMatCL,
                    map_object.logger,
                    args.mem,
                )
                # Descripteurs pour les couches de couleurs
                validation.computeDescriptors(map_object.confMatCL, map_object.logger)

            if os.path.isfile(map_object.objects):
                map_object.logger.message("reconstructed objects validation")
                # Matrice de confusion pour les objets reconstruits
                validation.computeConfusionMatrix(
                    map_object.objects,
                    map_object.valiData,
                    map_object.confMatObj,
                    map_object.logger,
                    args.mem,
                )
                # Descripteurs pour les objets reconstruits
                validation.computeDescriptors(map_object.confMatObj, map_object.logger)

        else:
            map_object.logger.message(
                "no validation data detected", console=True, warning=True
            )

    except:
        map_object.logger.message("validation error", console=True, warning=True)

    map_object.logger.message("job completed", console=True, warning=True)

    del map_object

    return


def parseArguments():
    # Paramètres de base
    parser = argparse.ArgumentParser(
        description="Vectorization of fluvial corridors on topographic maps"
    )
    parser.add_argument(
        "working_directory",
        help="Working directory which contains all the files/folders needed",
    )
    parser.add_argument(
        "-f",
        "--format",
        help="File extension of the images which will be analysed (default=tif)",
        default="[tT][iI][fF]",
    )
    parser.add_argument(
        "-v",
        "--valleybottom",
        help="Valley bottom file to compute masks (default=./valley_bottom/valley_bottom.shp)",
        default="./valley_bottom/valley_bottom.shp",
    )
    parser.add_argument("-i", "--image", help="Unique RGB map image to process")

    # Etapes de traitement à effectuer
    parser.add_argument("-m", "--mask", help="Create AC masks", action="store_true")
    parser.add_argument(
        "-l", "--lab", help="Convert RGB maps to CIE L*ab", action="store_true"
    )
    parser.add_argument(
        "-s",
        "--sample",
        help="Create color sample on the CIE L*lab map",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--classif",
        help="Classification method (if classification of map colors wanted)",
    )
    parser.add_argument(
        "-r",
        "--reconstruct",
        help="Reconstruction of fluvial corridor's objects",
        action="store_true",
    )

    # Passage des arguments
    args = parser.parse_args()

    # Calcul de la RAM disponible pour chaque tache (90% de la RAM disponible au lancement en Mb divisée par le nombre de taches)
    # TODO: voir si on peux mettre a jour cette valeur au fur et a mesure du traitement
    args.mem = psutil.virtual_memory()
    args.mem = (args.mem.available / 1000000) * 0.9

    return args


if __name__ == "__main__":
    # ------------------------
    # PARAMETRES AVEC ARGPARSE
    global args
    args = parseArguments()

    os.chdir(os.path.normpath(args.working_directory))

    # ------------------------
    # CREATION DU MAIN LOGGER
    mainlogger = CustomLogger("MainLogs")
    mainlogger.stepUpdate("Initialization")

    # ------------------------
    # LISTAGE DES CARTES A TRAITER
    if args.image == None:
        mainlogger.message("listing maps")
        mapList = []
        for fileRGB in glob.glob("./rgb/*.{}".format(args.format)):
            mapList.append(MapFiles(fileRGB, None, args.mem))

    # ------------------------
    # CHARGEMENT DU VALLEY BOTTOM
    global vb_features

    if os.path.isfile(args.valleybottom):
        with fiona.open(args.valleybottom, "r") as shapefile:
            mainlogger.message("reading valley bottom data")
            vb_features = [feature["geometry"] for feature in shapefile]
            shapefile.close()
    else:
        mainlogger.message(
            "valley bottom shapefile not found. Active channel masking will not be possible",
            console=True,
            warning=True,
        )
        pass

    mainlogger.message("--process is ready", console=True)

    # ------------------------
    # LANCEMENT DU TRAITEMENT
    if args.image == None:
        for mp in mapList:
            completeJob(mp)

    else:
        mainlogger.message("unique map processing")
        completeJob(MapFiles(args.image, None, args.mem))

    sys.exit(0)
