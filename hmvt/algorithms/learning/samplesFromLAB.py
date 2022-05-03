# -*- coding: utf-8 -*-

import rasterio
import numpy as np
import fiona
import cv2

from rasterio import features


def samplesFromLAB(lab_path, samples_path, vector_samples_path, logger):
    '''
    :type lab_path: str
    :type sample_path: str
    :type vector_samples_path: str
    :type logger: CustomLogger

    # TODO: Tester l'apport d'une condition de texture
    # TODO: Couleurs à détecter en fonction de type de légende
    # TODO: Réussir à gérer la classification des traits bleu foncé en noir (voir 313756)
    '''
    # ------------
    # Sampling

    logger.message("image reading")
    with rasterio.open(lab_path) as src:
        profile = src.profile.copy()
        profile.update({"count": 1, "dtype": rasterio.uint8})

        logger.message("reading lab data")
        # Ouverture des bandes
        lum = src.read(1)
        chromA = src.read(2)
        chromB = src.read(3)

    logger.message("radiometric selections")

    # Création des tuiles de samples
    sampleBlue = np.zeros(lum.shape)
    sampleGreen = np.zeros(lum.shape)
    sampleBlack = np.zeros(lum.shape)
    sampleWhite = np.zeros(lum.shape)
    sampleBistre = np.zeros(lum.shape)

    # Algèbre sur les bandes pour extraire les samples de base
    sampleBlack = (np.logical_and(lum > 0, lum < 4000))

    # Pour le blanc, on vérifie qu'au moins 25% de l'image répond au seuil, sinon on le diminue
    lum_threshold = 9500
    sampleWhite = (lum > lum_threshold)
    white_size = np.count_nonzero(sampleWhite)

    while white_size < 0.25*float(lum.size):
        lum_threshold -= 100
        sampleWhite = (lum > lum_threshold)
        white_size = np.count_nonzero(sampleWhite)
    
    logger.message("lum threshold used to detect white : {}".format(lum_threshold))
    del lum

    sampleBlue = np.logical_and(chromB < -500, sampleWhite == 0)
    sampleBlue = np.logical_and(sampleBlue == 1, sampleBlack == 0)

    sampleGreen = np.logical_and(chromA < 0, chromB > 0)
    sampleGreen = np.logical_and(
        sampleGreen == 1, sampleBlack == 0)
    sampleGreen = np.logical_and(
        sampleGreen == 1, sampleWhite == 0)

    sampleBistre = np.logical_and(chromA > 500, chromB > 500)
    del chromA, chromB

    sampleBistre = np.logical_and(
        sampleBistre == 1, sampleBlack == 0)
    sampleBistre = np.logical_and(
        sampleBistre == 1, sampleWhite == 0)   

    # Recodage des samples sur une bande
    full_samples = np.zeros(sampleBlue.shape, dtype=np.uint8)
    full_samples = (1*sampleBlack + 2*sampleWhite +
                3*sampleBlue + 4*sampleGreen + 5*sampleBistre)

    # Suppression des couches de samples
    del sampleBlue, sampleGreen, sampleBlack, sampleWhite, sampleBistre

    logger.message("erosions")
    # Création d'un array vide en sortie
    samples_ero = np.zeros(full_samples.shape, dtype=np.uint8)

    # Iteration sur les classes
    for id_class in range(1, 6):
        samples = np.zeros(full_samples.shape, dtype=np.uint8)
        samples = (full_samples == id_class)

        # Diminution progressive de l'élément structurant pour garder au minimum 1k pixels dans chaque classe
        eroded = np.zeros(samples.shape, dtype=np.uint8)
        radius = 8
        sample_size = 0
        while sample_size < 3000 and radius >= 1:
            strel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (radius, radius))
            eroded = cv2.erode(samples.astype("uint8"), strel)
            radius -= 1
            sample_size = np.count_nonzero(eroded)

        message = "class {}, radius {}: {} px in sample".format(
            str(id_class), str(radius+1), str(sample_size))
        logger.message(message)

        # Pour le vert, si le rayon d'érosion est inférieur à 6, on considere qu'il n'y a pas de vert
        if id_class == 4 and radius <= 6:
            logger.message("not enough green detected, removed from samples", console=True, warning=True)
            continue

        # Si il reste plus de 5k px en sample, sélection aléatoire
        # Si on veux limiter la qté en % de l'image plutôt qu'en qté brute, utiliser ça : max_size = 0.01*float(eroded.size)
        max_size = 5000
        mask = np.zeros(eroded.shape, dtype=np.uint8)
        while sample_size > max_size:
            if 1-(max_size/float(sample_size)) > 0.7:
                prob = 0.9
            else:
                prob = 0.5

            mask = np.random.choice([0, 1], size=eroded.shape, p=[prob, 1-prob])
            eroded = np.logical_and(eroded, mask)
            sample_size = np.count_nonzero(eroded)
            logger.message(
                "sample selection randomly reduced to "+str(sample_size)+" px")

        # Ajout des pixels selectionnés sur les samples en sortie
        samples_ero = (samples_ero + id_class*eroded)

    # Libération de mémoire
    del full_samples, samples, eroded, mask, strel

    # -------------------------
    # Vectorisation des samples

    logger.message("sample vectorization started")

    with rasterio.open(samples_path, "w", **profile) as dst:
        # Listage des entités
        mask = (samples_ero > 0)
        results = ({'properties': {'class': v}, 'geometry': s}
                   for i, (s, v) in enumerate(features.shapes(samples_ero.astype(rasterio.uint8), mask=mask, transform=dst.transform)))
        
        del mask

        with fiona.open(vector_samples_path, "w", driver="Shapefile", crs=dst.crs, schema={'properties': [('class', 'int')],
                                                                                           'geometry': 'Polygon'}) as v_dst:
            logger.message("writing samples data")
            # Enregistrement du raster
            logger.message("---raster data")
            dst.write(samples_ero.astype(rasterio.uint8), 1)
            del samples_ero

            # Enregistrement des vecteurs
            logger.message("---vector data")
            v_dst.writerecords(results)
            del results
 
    return