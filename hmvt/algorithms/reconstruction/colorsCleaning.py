# -*- coding: utf-8 -*-

import cv2
from skimage.morphology import remove_small_objects


def colorsCleaning(img, logger):
    """
    Nettoyage des couches de couleur pour reconstruction
    """
    logger.message("opening color layers")

    black = img == 1
    blue = img == 3
    green = img == 4
    bistre = img == 5

    # Gestion des pixels mixtes en bordure du noir
    logger.message("mixed pixel masking")
    # Nettoyage par tamisage puis propagation du noir sur 5 pixels
    black = remove_small_objects(black.astype("bool"), 5)

    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    black_dil = cv2.dilate(black.astype("uint8"), strel)

    # Propagation uniquement sur les pixels bleu, vert ou bistre
    black = black | (black_dil & (blue | green | bistre))

    # Filtrage des couches bleu, vert et bistre par rapport au nouveau noir
    blue = blue & ~black.astype("bool")
    green = green & ~black.astype("bool")
    bistre = bistre & ~black.astype("bool")

    # Nettoyage par tamisage des couches de couleurs
    logger.message("cleaning color layers")
    black = remove_small_objects(black.astype("bool"), 10)
    blue = remove_small_objects(blue.astype("bool"), 10)
    green = remove_small_objects(green.astype("bool"), 50)
    bistre = remove_small_objects(bistre.astype("bool"), 50)

    return black, blue, green, bistre
