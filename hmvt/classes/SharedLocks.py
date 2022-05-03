# -*- coding: utf-8 -*-
"""
***************************************************************************
    SharedLocks.py
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

import sys
import multiprocessing
import psutil
import time

from classes import CustomLogger

RQueue = multiprocessing.RLock()
RWLock = multiprocessing.RLock()

ReadLock = multiprocessing.RLock()
WriteLock = multiprocessing.RLock()
OTBLock = multiprocessing.Lock()

NoLock = False


# class IOLock:
#     '''
#     Classe utilisable en with statement. Verrou de lecture/écriture avec priorité faible aux writers.
#     '''
#     def __init__(self, LockMode, logger=None):
#         self.mode = LockMode
#         self.logger = logger

#     def __enter__(self):
#         if self.logger:
#             self.logger.message("waiting for "+self.mode+" lock", console=True)

#         if self.mode == "r":
#             with RQueue:
#                 RWLock.acquire()

#         elif self.mode == "w":
#             RWLock.acquire()

#         else:
#             if self.logger:
#                 self.logger.message("unrecognized lock mode", warning=True, console=True)
#             else:
#                 print("unrecognized lock mode")
            
#             sys.exit(1)

#         if self.logger:
#             self.logger.message(self.mode+" lock acquired", console=True)

#     def __exit__(self, type, value, traceback):
#         if self.logger:
#             self.logger.message(self.mode+" lock released", console=True)

#         RWLock.release()


class IOLock:
    '''
    Classe utilisable en with statement. Gestion de 3 verrous indépendants:
    - RLock pour la lecture
    - WLock pour l'écriture
    - OTBLock pour otb uniquement

    Possibilité d'ajouter une condition de mémoire vive dispo pour les opérations gourmandes
    '''
    def __init__(self, LockMode, logger=None, memory=None):
        '''
        :type LockMode: str
        :type logger: CustomLogger
        :type memory: int
        '''
        self.mode = LockMode
        self.logger = logger
        self.memory = memory

        if self.mode == "w":
            self.memory = None

    def __enter__(self):
        if NoLock:
            if self.logger:
                self.logger.message("no r/w lock option")

        else:
            if self.logger:
                self.logger.message("waiting for "+self.mode+" lock", console=True)

            if self.mode == "r":
                ReadLock.acquire()
            elif self.mode == "w":
                WriteLock.acquire()
            elif self.mode == "otb":
                OTBLock.acquire()
            else:
                if self.logger:
                    self.logger.message("unrecognized lock mode", warning=True, console=True)
                else:
                    print("unrecognized lock mode")
                
                sys.exit(1)

            if self.logger:
                self.logger.message(self.mode+" lock acquired", console=True)

            if self.memory:
                mem = psutil.virtual_memory()
                if mem.available < self.memory:
                    self.logger.message("waiting for virtual memory", console=True)
                    timer = 0
                    while (mem.available < self.memory) & (timer < 1800):
                        time.sleep(3)
                        timer += 3
                        mem = psutil.virtual_memory()
                    
                    self.logger.message("virtual memory sufficient, process unlocked", console=True)


    def __exit__(self, type, value, traceback):
        if NoLock:
            if self.logger:
                self.logger.message("no r/w lock option")
        
        else:
            if self.logger:
                self.logger.message(self.mode+" lock released", console=True)

            if self.mode == "r":
                ReadLock.release()
            elif self.mode == "w":
                WriteLock.release()
            elif self.mode == "otb":
                OTBLock.release()