# -*- coding: utf-8 -*-

from multiprocessing import cpu_count

from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
import rasterio


def rfClassification(lab_raster, samples_raster, colors_raster, logger=None):
    logger.message("...read lab data")
    with rasterio.open(lab_raster) as src:
        profile = src.profile.copy()
        profile.update({"count": 1, "dtype": rasterio.uint8})

        # logger.message("reading lab data")
        # Ouverture des bandes
        data = {'L': np.ravel(src.read(1)), 'a': np.ravel(src.read(2)), 'b': np.ravel(src.read(3))}

    data = pd.DataFrame(data)

    logger.message("...read samples data")
    with rasterio.open(samples_raster) as src:
        # logger.message("reading samples data")
        # Ouverture des bandes
        data['class'] = np.ravel(src.read(1))

    trainData = data.loc[data['class'] != 0]

    y = trainData["class"]
    X = trainData[trainData.columns.difference(["class"])]

    model = RandomForestClassifier(n_estimators=750, max_features=3, oob_score=True)

    model.set_params(n_jobs=int(cpu_count()/2))
    logger.message("...train knn classifier")
    model.fit(X, y)

    logger.message("...classify data")
    data["predicted"] = model.predict(data[data.columns.difference(["class"])])
    
    logger.message("...write color layers")
    with rasterio.open(colors_raster, "w", **profile) as dst:
        dst.write(data["predicted"].values.reshape(dst.shape).astype(rasterio.uint8), 1)

    return