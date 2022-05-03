# -*- coding: utf-8 -*-

import shapely.ops
import numpy as np
import pandas as pd
import geopandas as gpd

from shapely.geometry import Point, LineString
from scipy.spatial import cKDTree


def vectorizeLines(objects_array, src):
    """
    Vectorize lines on objects np array
    """
    # Liste des coordonnées des poitns à relier
    coords = np.where(objects_array == 4)
    coords_arr = np.array(list(zip(*coords)))

    # Construction du graph
    tree = cKDTree(coords_arr)

    # Recherche des points à moins de 1.5px de chaque point
    prox = tree.query_ball_point(coords_arr, 1.5)

    # Création d'un liste de liens à créer
    rownum = 1
    pts = []
    for FROM, dest_list in enumerate(prox):
        for TO in dest_list:
            # Pour éviter les doublons, on vérifie que l'id de FROM est > à celui de TO
            if FROM > TO:
                ptFROM = Point(src.xy(*coords_arr[FROM]))
                ptTO = Point(src.xy(*coords_arr[TO]))
                linestring = LineString([ptFROM, ptTO])

                pts.append([rownum, linestring])
                rownum += 1

    # Création d'un géodataframe avec les liens entre chaque point
    linksGDF = gpd.GeoDataFrame(
        pts, crs=src.crs, columns=["ID", "geometry"], geometry="geometry"
    )

    # Dissolve des liens
    union = linksGDF.unary_union
    merge = shapely.ops.linemerge(union)
    lines = [(i, g) for i, g in enumerate(merge)]

    linesGDF = gpd.GeoDataFrame(
        lines, crs=src.crs, columns=["ID", "geometry"], geometry="geometry"
    )

    # Gestion des jonctions en T et en X
    # Sélection des lignes inférieures à 1.5px
    linesGDF["length"] = linesGDF.geometry.length
    juncGDF = linesGDF[(linesGDF.length <= 1.5)]
    linesGDF = linesGDF[(linesGDF.length >= 1.5)]

    # Buffer et dissolve sur ces lignes
    juncGDF = juncGDF.buffer(2, resolution=1)
    union = juncGDF.unary_union

    junc = [(i, g) for i, g in enumerate(union.geoms)]
    juncGDF = gpd.GeoDataFrame(
        junc, crs=src.crs, columns=["ID", "geometry"], geometry="geometry"
    )

    # Extraction des centroides des polygones de jonctions
    juncGDF = juncGDF.centroid
    junc = [list(g.coords)[0] for g in juncGDF.geometry]
    junc = np.array(junc)

    # Extraction des extreme points des lignes
    ext_pts = [list(g.coords)[0] for g in linesGDF.geometry]
    ext_pts.extend([list(g.coords)[-1] for g in linesGDF.geometry])
    ext_pts = np.array(ext_pts)

    # Connexion des jonctions aux extreme points les plus proches
    tree = cKDTree(junc)
    prox = tree.query_ball_point(ext_pts, 1.5 * src.res[0])

    junc_lines = []
    for FROM, dest_list in enumerate(prox):
        for TO in dest_list:
            if FROM > TO:
                ptFROM = Point(ext_pts[FROM])
                ptTO = Point(junc[TO])
                linestring = LineString([ptFROM, ptTO])

                junc_lines.append([rownum, linestring])
                rownum += 1

    juncGDF = gpd.GeoDataFrame(
        junc_lines, crs=src.crs, columns=["ID", "geometry"], geometry="geometry"
    )

    linesGDF.drop("length", axis=1)
    linksGDF = pd.concat([linesGDF.drop("length", axis=1), juncGDF], axis=0)

    # Dissolve des jonctions avec les lignes principales
    union = linksGDF.unary_union
    merge = shapely.ops.linemerge(union)

    lines = [(i, g) for i, g in enumerate(merge)]
    linesGDF = gpd.GeoDataFrame(
        lines, crs=src.crs, columns=["ID", "geometry"], geometry="geometry"
    )

    return linesGDF
