# -*- coding: utf-8 -*-

import cv2


def overlayZone(black, bistre, logger):
    """
    Calcul de la zone de superposition (pour les ponts notamment)
    """
    logger.message("reconstruction zone computing")
    # Fermetures du noir et du bistre pour créer une zone de reconstruction
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
    black_close = cv2.morphologyEx(black.astype("uint8"), cv2.MORPH_CLOSE, strel)

    overlay_zone = black_close | bistre

    return overlay_zone
