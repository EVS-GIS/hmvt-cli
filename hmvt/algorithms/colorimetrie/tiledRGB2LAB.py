# -*- coding: utf-8 -*-

import rasterio
import cv2
import numpy as np


def tiledRGB2LAB(path_rgb, path_lab):
    """
    :type path_rgb: str
    :type path_lab: str

    TODO: les blocks sont trop petits. Il faudrait définir une taille de bloc (1/8 d'image par ex) et faire une boucle à la main
    """

    with rasterio.open(path_rgb) as src:
        profile = src.profile.copy()
        profile.update({"dtype": rasterio.int16})

        with rasterio.open(path_lab, "w", **profile) as dst:
            # Traitement par bloc de l'image source
            for block_index, window in src.block_windows(1):

                img = src.read(window=window)

                img = np.swapaxes(img, 0, 2)
                img = img.astype("float32") * 1.0 / 255
                img = cv2.cvtColor(img, cv2.COLOR_RGB2Lab)
                img = np.swapaxes(img, 2, 0)

                # Conversion en entier 16bits
                img = (img * 100).astype("int16")

                dst.write(img, window=window)

    return
