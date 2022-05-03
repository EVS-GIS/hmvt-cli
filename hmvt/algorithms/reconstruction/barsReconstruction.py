# -*- coding: utf-8 -*-

import cv2
import numpy as np

from skimage.morphology import remove_small_holes, remove_small_objects
from skimage.measure import label, regionprops


def barsReconstruction(bars_part, water_surf, water_lines, logger):
    logger.message("bars reconstruction")
    logger.message("...ac reconstruction")
    act_channel = bars_part | water_surf
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    act_channel = cv2.morphologyEx(act_channel.astype("uint8"), cv2.MORPH_CLOSE, strel)

    logger.message("...potential bars extraction")
    bars = act_channel & ~water_surf.astype("bool")
    bars = bars & ~water_lines.astype("bool")
    del act_channel

    logger.message("...first cleaning")
    bars = remove_small_objects(bars.astype("bool"), 800)
    bars = remove_small_holes(bars.astype("bool"), 500)

    logger.message("...objects selection")
    logger.message("......label potential bars")
    lbl, nregions = label(bars, connectivity=2, return_num=True)

    logger.message("......compute props")
    regions = regionprops(lbl, intensity_image=bars_part)

    logger.message("......filter objects")
    bars = np.zeros(bars.shape, dtype="bool")
    for obj in regions:
        px_num = np.count_nonzero(obj.intensity_image)
        if px_num > 50:
            bars = bars | (lbl == obj.label)
        else:
            pass

    del lbl

    logger.message("...final cleaning")
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    bars = cv2.morphologyEx(bars.astype("uint8"), cv2.MORPH_OPEN, strel)
    bars = remove_small_objects(bars.astype("bool"), 1000)
    bars = remove_small_holes(bars.astype("bool"), 500)
    bars = bars & ~water_lines
    bars = bars & ~water_surf

    return bars
