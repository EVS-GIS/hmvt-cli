# -*- coding: utf-8 -*-

import copy
import rasterio
import cv2

import numpy as np
import pandas as pd

from rasterio import features
from skimage.measure import label, regionprops_table
from multiprocessing import cpu_count

import lib
import sys

def particlesClassification(particles, water_surf, lab_layer, logger, group_size=50, return_objects=False, profile=None):
    """
    Classification RandomForest des particules de bleu restantes
    """
    logger.message("particles OBIA classification")

    # Variables à utiliser pour la RF
    variables = [
        "area",
        "bbox_area",
        "convex_area",
        "eccentricity",
        "equivalent_diameter",
        "euler_number",
        "extent",
        "filled_area",
        "major_axis_length",
        "minor_axis_length",
        "orientation",
        "perimeter",
        "solidity",
    ]

    # Rajout du label
    variables.append("label")

    # Regroupement des particules bleues en groupes
    logger.message("...regroup particles")
    strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (group_size, group_size))
    particles_groups = cv2.morphologyEx(
        particles.astype("uint8"), cv2.MORPH_CLOSE, strel
    )
    particles_groups = (particles_groups & ~water_surf)

    # Propriétés des groupes
    logger.message("...label groups")
    particles_groups, nregions = label(particles_groups, connectivity=2, return_num=True)

    logger.message("...compute groups props")
    regions = regionprops_table(particles_groups, properties=variables)

    g_props = pd.DataFrame(regions).add_prefix("g_").set_index("g_label")

    # Propriétés des particules bleues
    logger.message("...label particles")
    particles, nregions = label(particles, connectivity=2, return_num=True)

    # On rajoute max_intensity pour récupérer l'id du groupe auquel appartient la particule
    variables.append("max_intensity")

    logger.message("...compute particles props")
    regions = regionprops_table(particles, intensity_image=particles_groups, properties=variables)

    p_props = pd.DataFrame(regions)
    p_props["max_intensity"] = p_props["max_intensity"].astype("int")
    p_props = p_props.rename({"max_intensity": "g_label"}, axis="columns")

    # Calcul des moyennes L*ab pour les groupes et les particules
    logger.message("...open lab layer")
    with rasterio.open(lab_layer) as src:
        layers = ["L", "a", "b"]
        n = [1, 2, 3]

        # Moyennes pour les groupes
        for i, j in zip(layers, n):
            regions = regionprops_table(particles_groups, intensity_image=src.read(j), properties=["label", "min_intensity", "mean_intensity", "max_intensity"])
            regions = pd.DataFrame(regions)

            regions = regions.rename({
                "label": "g_label",
                "min_intensity": "g_min_"+i,
                "mean_intensity": "g_mean_"+i,
                "max_intensity": "g_max_"+i,
                }, axis="columns")

            g_props = pd.merge(g_props, regions, on="g_label")

        # Moyennes pour les particules
        for i, j in zip(layers, n):
            regions = regionprops_table(particles, intensity_image=src.read(j), properties=["label", "min_intensity", "mean_intensity", "max_intensity"])
            regions = pd.DataFrame(regions)

            regions = regions.rename({
                "min_intensity": "min_"+i,
                "mean_intensity": "mean_"+i,
                "max_intensity": "max_"+i,
                }, axis="columns")

            p_props = pd.merge(p_props, regions, on="label")

    # Regroupement des données des groupes et des particules
    logger.message("...join group data to particle data")
    props = pd.merge(p_props, g_props, on="g_label")

    # Calcul de deux variables supplémentaires par groupe : size (qté de particules) et surf (qté de pixels pleins)
    logger.message("...compute last group variables")
    g_props = props.groupby(["g_label"]).count()
    g_props = g_props.rename({"area": "g_size"}, axis="columns")
    props = pd.merge(props, g_props[["g_size"]], on="g_label")

    g_props = props.groupby(["g_label"]).sum()
    g_props = g_props.rename({"area": "g_surf"}, axis="columns")
    props = pd.merge(props, g_props[["g_surf"]], on="g_label")

    props = props.set_index("label")

    # Export des données pour préparer le modèle RF (si passé en paramètre)
    if return_objects:
        types = zip(props.dtypes.index, props.dtypes)
        types = [(x, y.name) for x, y in types]
        types = [(x, y.replace("int64", "int")) for x, y in types]
        types = [(x, y.replace("float64", "float")) for x, y in types]

        logger.message("...export objects")

        p_props = props.to_dict("index")
        results = (
            {"properties": p_props[v], "geometry": s}
            for i, (s, v) in enumerate(
                features.shapes(
                    particles.astype(rasterio.int32),
                    mask=np.isin(particles, props.index),
                    transform=profile.get("transform"),
                    connectivity=8,
                )
            )
        )

        return types, results

    # Le tableau de données est prêt, on peut lancer le modèle RF
    logger.message("...prepare RF model")
    props = props[props.columns.difference(["g_label"])]
    model = copy.copy(lib.RFModel)
    njobs = int(cpu_count() / 2)
    model.set_params(n_jobs=njobs)

    logger.message("...predict particle class with RF model")
    props["predicted"] = model.predict(props)

    del model

    # Report du résultat de la classification sur la matrice bleue
    logger.message("...translate result into matrix")
    linear_labels = props[props["predicted"] == 1].index
    bar_labels = props[props["predicted"] == 2].index

    linear = np.isin(particles, linear_labels)
    bars = np.isin(particles, bar_labels)

    return bars, linear
