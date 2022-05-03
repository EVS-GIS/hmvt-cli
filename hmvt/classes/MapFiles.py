# -*- coding: utf-8 -*-
"""
***************************************************************************
    main.py
    ---------------------
    Date                 : 2018
    Copyright            : (C) 2018 by Samuel Dunesme
***************************************************************************
*                                                                         *
*                                                                         *
***************************************************************************
"""

__author__ = "Samuel Dunesme"
__date__ = "2018"
__copyright__ = "(C) 2018, Samuel Dunesme"

import os
from classes import CustomLogger


class MapFiles:
    def __init__(self, rgbFile, pathJPG, mem):
        # Paramétrage des chemins de fichiers en fonction du chemin du fichier RGB
        # Normalisation du chemin RGB et extraction nom image, format, date
        self.rgb = os.path.normpath(rgbFile)
        self.memory = str(mem)

        temp_name = os.path.split(self.rgb)[1]
        self.name, self.format_image = temp_name.split(".")
        # self.date = self.name.split("_")[2]

        self.logger = CustomLogger(self.name)

        self.logger.message(self.memory + " Mb available")
        self.logger.message("paths initialisation")

        # Paramétrage des chemins
        self.lab = "./lab/" + self.name + "_lab." + self.format_image
        self.yelCorr = "./lab/" + self.name + "_yelCorr." + self.format_image
        self.mask = "./masks/" + self.name + "_msk." + self.format_image
        self.samples = "./samples/" + self.name + "_samples." + self.format_image
        self.sampleShapes = "./samples/" + self.name + "_samples.shp"
        self.classifModel = "./classifModels/" + self.name + "_model.txt"
        self.colorLayers = "./colorLayers/" + self.name + "_CL." + self.format_image
        self.objects = "./objects/" + self.name + "_objects." + self.format_image
        self.polygonalObjects = "./polygonalObjects/" + self.name + "_surfaces.shp"
        self.linearObjects = "./polygonalObjects/" + self.name + "_lines.shp"
        self.valiData = "./validation_data/" + self.name + ".shp"
        self.confMatModel = "./dataTest/" + self.name + "_model.csv"
        self.confMatCL = "./dataTest/" + self.name + "_CL.csv"
        self.confMatObj = "./dataTest/" + self.name + "_objects.csv"

        # Vérification qu'il existe un fichier JPG correspondant dans le pathJPG
        if pathJPG == None:
            self.jpg = None
            self.logger.message("no parametrized jpg path")
        else:
            self.jpg = os.path.join(os.path.normpath(pathJPG), self.name + ".jpg")
            if not os.path.isfile(self.jpg):
                self.jpg = None
                self.logger.message(
                    self.name + " : fichier JPG introuvable", console=True, warning=True
                )

        # Création des folders si ils n'existent pas
        dirlist = [
            "./lab",
            "./masks",
            "./samples",
            "./classifModels",
            "./colorLayers",
            "./objects",
            "./dataTest",
            "./polygonalObjects",
        ]
        [os.mkdir(dirpath) for dirpath in dirlist if not os.path.isdir(dirpath)]

        return
