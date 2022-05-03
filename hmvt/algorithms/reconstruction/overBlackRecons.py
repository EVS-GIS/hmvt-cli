# -*- coding: utf-8 -*-

from skimage.filters import rank
from skimage.morphology import disk


def overBlackRecons(black, blue, green, bistre, logger):
    """
    Reconstruction sur le noir par majority voting (filtre modal)
    """
    logger.message("reconstruction over black layer")
    # Regroupement des couleurs dans une image
    img = black + 2 * blue + 3 * green + 4 * bistre
    # Filtre modal de rayon 20px en excluant la valeur du noir via un masque
    img = rank.modal(img.astype("uint8"), disk(20), mask=(img != 1))

    # Masquage pour ne filtrer que les zones anciennement noir
    img = black * img

    # Séparation des couleurs en sortie
    blue = (img == 2) | blue
    green = (img == 3) | green
    bistre = (img == 4) | bistre

    return blue, green, bistre
