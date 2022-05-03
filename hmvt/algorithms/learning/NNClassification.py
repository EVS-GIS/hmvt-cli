# -*- coding: utf-8 -*-

from multiprocessing import cpu_count

import numpy as np
import pandas as pd
import rasterio
import cv2


def knnClassification(lab_raster, samples_raster, colors_raster, logger=None, mask_raster=None):

    logger.message("...read lab data")
    with rasterio.open(lab_raster) as src:
        profile = src.profile.copy()
        profile.update({"count": 1, "dtype": rasterio.uint8})
        # Ouverture des bandes
        data = {
            "L": np.ravel(src.read(1)).astype(np.float32),
            "a": np.ravel(src.read(2)).astype(np.float32),
            "b": np.ravel(src.read(3)).astype(np.float32),
        }

    data = pd.DataFrame(data)

    if mask_raster:
        logger.message("...read mask data")
        with rasterio.open(mask_raster) as src:
            data["msk"] = np.ravel(src.read(1))  
    else:
        data["msk"] = 1

    logger.message("...read samples data")
    with rasterio.open(samples_raster) as src:
        # Ouverture des bandes
        data["class"] = np.ravel(src.read(1))

    trainData = data.loc[data["class"] != 0]

    y = trainData["class"].to_numpy().reshape(-1,1).astype(np.float32)
    X = trainData[trainData.columns.difference(["class", "msk"])].to_numpy()

    model = cv2.ml.KNearest_create()
    model.setDefaultK(32)
    
    logger.message("...train knn classifier")
    model.train(X, cv2.ml.ROW_SAMPLE, y)

    logger.message("...mask data")
    mdata = data.loc[data["msk"]==1]
    mdata = mdata[mdata.columns.difference(["class", "msk"])]

    logger.message("...classify data")
    ret, mdata["predicted"], nei, dist = model.findNearest(mdata.to_numpy(), k=32)

    mdata = mdata.reindex(data.index)

    logger.message("...write color layers")
    with rasterio.open(colors_raster, "w", **profile) as dst:
        dst.write(mdata["predicted"].values.reshape(dst.shape).astype(rasterio.uint8), 1)

    return
