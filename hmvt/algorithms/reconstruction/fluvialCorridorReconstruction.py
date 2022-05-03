# -*- coding: utf-8 -*-

import rasterio
import cv2
import fiona
import numpy as np
from rasterio import features
from skimage.morphology import remove_small_objects, skeletonize

from algorithms import reconstruction

def fluvialCorridorReconstruction(classif_img, lab_layer, objects_img_out, polygonalObjectsOut, linearObjectsOut, logger=None):
    """
    Reconstruction des objets du corridor fluvial à partir de calques de 
    couleur classifiés

    Args:
        classif_img: classification image file path
        objects_img_out: out objects image file path
        polygonalObjectsOut: out objects shapefile file path
        logger: logger object where the log will be written

    Returns:
        Nothing
    """

    if not logger:
        from classes.CustomLogger import CustomLogger
        logger = CustomLogger("MorphoRecons")

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
    black = (black & ~(blue.astype("bool") |
                        green.astype("bool") | bistre.astype("bool")))
    logger.message("...done")

    # Calcul de la zone de reconstruction supplémentaire
    overlay_zone = reconstruction.overlayZone(black, bistre, logger)

    # Reconstruction des surfaces en eau
    water_surf = reconstruction.wsReconstruction(blue, overlay_zone, logger)

    # Mise à jour de la couche de bleu (soustraction de la WS)
    logger.message("...blue layer update")
    blue = (blue & ~water_surf.astype("bool"))
    blue = remove_small_objects(blue.astype("bool"), 10)
    logger.message("...update done")

# Classification OBIA des particules de bleu restantes
    logger.message("...blue particles")
    bars, water_lines = reconstruction.particlesClassification(blue, water_surf, lab_layer, logger=logger, group_size=50, return_objects=False)
    del blue

# Reconstruction et nettoyage des lignes
    logger.message("water lines reconstruction")
    logger.message("...close lines")
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    water_lines = cv2.morphologyEx(water_lines.astype("uint8"), cv2.MORPH_CLOSE, strel) 

    logger.message("...skeletonize result")
    # water_lines = opencvSkeletonization(water_lines)
    water_lines = skeletonize(water_lines)

    logger.message("...water lines cleaning")
    water_lines = remove_small_objects(water_lines.astype("bool"), 20, connectivity=8)

    logger.message("...water lines update")
    water_lines = (water_lines & ~water_surf)

# Reconstruction des bancs
    bars = reconstruction.barsReconstruction(bars, water_surf, water_lines, logger)

# Reconstruction de la végétation
    green = reconstruction.vegetReconstruction(green, overlay_zone, logger)

    # Mise à jour de la classe bancs par rapport a la végétation
    # logger.message("...bars layer update")
    # bars = (bars & ~green.astype("bool"))
    # logger.message("...update done")

    # Mise à jour de la classe végétation par rapport au linéaire et ws
    logger.message("...green layer update")
    green = (green & ~(water_surf.astype("bool") | water_lines.astype("bool")))
    green = (green & ~bars.astype("bool"))
    logger.message("...update done")

# Génération du raster en sortie
    logger.message("out objects raster generation")

    objects = (water_surf + 2*bars + 3*green + 4*water_lines)
    with rasterio.open(objects_img_out, "w", **profile) as dst:
        dst.write(objects.astype(rasterio.uint8), 1)
        dst.close()

# Génération des vecteurs en sortie
    logger.message("out objects vectors generation")
    logger.message("..polygonal objects")

    mask = np.logical_and(objects > 0, objects != 4)

    results = ({'properties': {'class': v}, 'geometry': s}
                for i, (s, v) in enumerate(features.shapes(objects.astype(rasterio.uint8), mask=mask, transform=profile.get("transform"))))
    
    del mask

    with fiona.open(polygonalObjectsOut, "w", driver="Shapefile", crs=profile.get("crs"), schema={'properties': [('class', 'int')],
                                                                                        'geometry': 'Polygon'}) as v_dst:
        v_dst.writerecords(results)
        del results
        v_dst.close()

    logger.message("..linear objects")
    linesObjects = reconstruction.vectorizeLines(objects, src)
    linesObjects.to_file(linearObjectsOut)

    return