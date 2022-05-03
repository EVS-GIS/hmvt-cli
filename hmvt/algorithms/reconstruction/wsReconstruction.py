# -*- coding: utf-8 -*-

import cv2

from skimage.morphology import remove_small_holes, remove_small_objects


def wsReconstruction(blue, overlay_zone, logger):
    """
    fonction TODO: A OPTIMISER
    """
    logger.message("water surfaces reconstruction")
    logger.message("...remove small objects")
    water_surf = remove_small_objects(blue.astype("bool"), 500)

    # Reconstruction des surfaces d'eau
    logger.message("...reconstruction over superposed colors")
    # Fermeture puis filtrage par rapport à la zone de reconstruction
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
    ws_recons = cv2.morphologyEx(water_surf.astype("uint8"), cv2.MORPH_CLOSE, strel)
    ws_recons = overlay_zone & ws_recons

    water_surf = water_surf.astype("bool") | ws_recons.astype("bool")
    del ws_recons

    logger.message("...results cleaning")
    # Nettoyage des trous dans les surfaces
    water_surf = remove_small_holes(water_surf.astype("bool"), 50)

    # Nettoyage des bordures des surfaces par ouverture
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    water_surf = cv2.morphologyEx(water_surf.astype("uint8"), cv2.MORPH_OPEN, strel)
    water_surf = remove_small_objects(water_surf.astype("bool"), 1000)

    return water_surf
