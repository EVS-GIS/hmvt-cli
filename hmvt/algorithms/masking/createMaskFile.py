# -*- coding: utf-8 -*-

import warnings
import rasterio
import rasterio.mask


def createMaskFile(rgb_path, mask_path, vb_features, logger):
    '''
    :type rgb_path: str
    :type mask_path: str
    :type vb_features: list
    :type logger: CustomLogger

    Cette fonction teste si un fond de vallée existe pour la carte et
    créé un masque du fond de vallée
    '''

    with rasterio.open(rgb_path) as src:
        profile = src.profile.copy()
        profile.update(
            {"count": 1,
             "dtype": rasterio.uint8})

        with warnings.catch_warnings():
            warnings.filterwarnings("error")

            try:
                logger.message("creating image mask")
                mask_img, out_transform, window = rasterio.mask.raster_geometry_mask(
                    src, vb_features, invert=True)

            except Warning:
                logger.message(
                    "no valley bottom available for this zone", console=True, warning=True)
                
                mask_img = src.read_masks(1)/255

        src.close()

    logger.message("writing mask")
    with rasterio.open(mask_path, "w", **profile) as dst:
        dst.write(mask_img.astype(rasterio.uint8), 1)
        dst.close()

    return