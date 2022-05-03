# -*- coding: utf-8 -*-
"""
***************************************************************************
prepareRFdata.py
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

Prepare data for a Random Forest fitting
"""

import glob
import os
import argparse

import fiona
import rasterio
from skimage.morphology import remove_small_objects

from algorithms import reconstruction
from classes import CustomLogger

def parseArguments():
    parser = argparse.ArgumentParser(
        description="Prepare blue particles data for Random Forest fitting")

    parser.add_argument("-cl", help="Color layers directory", required=True)
    parser.add_argument("-out", help="Output shp directory", required=True)
    parser.add_argument("-lab", help="L*ab layers directory", required=True)

    # Passage des arguments
    return parser.parse_args()


if __name__ == "__main__":
    # On parse les arguments et on prépare les options choisies
    args = parseArguments()

    dr = os.path.normpath(args.cl)
    CL_list = [os.path.join(dr, path) for path in os.listdir(dr)]
    CL_list.sort()

    dr = os.path.normpath(args.lab)
    LAB_list = [os.path.join(dr, path) for path in os.listdir(dr)]
    LAB_list.sort()

    SHP_path = os.path.normpath(args.out)
    logger = CustomLogger("prepareRFdata")

    for classif_img, lab_img in zip(CL_list, LAB_list):
        logger.stepUpdate(os.path.basename(classif_img))
        logger.beginTest()

        with rasterio.open(classif_img) as src:
            # Nettoyage initial des couleurs
            img = src.read(1)
            black, blue, green, bistre = reconstruction.colorsCleaning(img, logger)
            del img

            profile = src.profile.copy()

        # Reconstruction sur le noir
        blue, green, bistre = reconstruction.overBlackRecons(black, blue, green, bistre, logger)

        # Mise à jour du noir
        logger.message("...black layer update")
        black = black & ~(
            blue.astype("bool") | green.astype("bool") | bistre.astype("bool")
        )
        logger.message("...done")
        del green

        # Calcul de la zone de reconstruction supplémentaire
        recons_zone = reconstruction.overlayZone(black, bistre, logger)
        del black, bistre

        # Reconstruction des surfaces en eau
        water_surf = reconstruction.wsReconstruction(blue, recons_zone, logger)
        del recons_zone

        # Mise à jour de la couche de bleu (soustraction de la WS)
        logger.message("...blue layer update")
        blue = blue & ~water_surf.astype("bool")
        blue = remove_small_objects(blue.astype("bool"), 10)
        logger.message("...update done")
        del water_surf

        # Extraction des particules bleues restantes
        logger.resetTest()
        types, results = reconstruction.particlesClassification(
            blue, lab_img, logger=logger, return_objects=True, profile=profile
        )
        del blue

        shp_out = os.path.join(
            SHP_path, os.path.basename(os.path.splitext(classif_img)[0] + ".shp")
        )

        with fiona.open(
            shp_out,
            "w",
            driver="Shapefile",
            crs=profile.get("crs"),
            schema={"properties": types, "geometry": "Polygon"},
        ) as dst:

            dst.writerecords(results)

        logger.message("...shapefile written to " + shp_out)

        logger.stopTest()
