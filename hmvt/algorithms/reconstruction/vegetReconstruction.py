# -*- coding: utf-8 -*-

import cv2

from skimage.morphology import remove_small_holes
from skimage.morphology import remove_small_objects


def vegetReconstruction(green, overlay_zone, logger):
    """
    Reconstruction de la végétation
    """
    logger.message("vegetation reconstruction")

    green = remove_small_holes(green.astype("bool"), 20)
    # Ouverture pour nettoyer les particules non pertinentes
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    green = cv2.morphologyEx(green.astype("uint8"), cv2.MORPH_OPEN, strel)

    logger.message("...over superposed colors")
    # Fermeture puis filtrage par rapport à la zone de reconstruction
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    green_close = cv2.morphologyEx(green.astype("uint8"), cv2.MORPH_CLOSE, strel)
    green_close = overlay_zone & green_close

    green = green | green_close
    del green_close

    logger.message("...general reconstruction")

    # Remplissage des trous
    green = remove_small_holes(green.astype("bool"), 80)


    # Fermeture
    # strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    # green = cv2.morphologyEx(green.astype("uint8"), cv2.MORPH_CLOSE, strel)

    # Remplissage des trous restants par tamisage
    green = remove_small_holes(green.astype("bool"), 200)

    return green
