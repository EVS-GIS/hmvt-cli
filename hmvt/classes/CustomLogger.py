# -*- coding: utf-8 -*-
"""
***************************************************************************
    CustomLogger.py
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
from time import strftime, time, gmtime


class CustomLogger:
    def __init__(self, image_name):
        """
        Initialize logger
        """

        self.name = str(image_name)
        self.log_path = "./logs/" + self.name + ".txt"
        self.stepMsg = "Initialization"
        self.start = time()
        self.steps = []
        self.alwaysConsole = False

        # Création du folder si il n'existe pas
        if not os.path.isdir("./logs"):
            os.mkdir("./logs")

    def resetTimer(self):
        self.start = time()
        self.timer = 0
        return

    def message(self, message, console=False, warning=False):
        """
        Send message to logger.

        Parameters:

            :param message: message to send
            :param console: return message to stdout
            :param warning: message is a warning
            :type message: any
            :type console: bool
            :type warning: bool

        Return: nothing
        """

        self.timer = time() - self.start
        self.txtTimer = strftime("%Hh%M'%S\"", gmtime(self.timer))

        file_msg = "[{tm}]({tmr}) {name:^15} [{step:^14}]: {msg}\n".format(
            tm=strftime("%m-%d %H:%M:%S"),
            tmr=self.txtTimer,
            name=self.name,
            step=self.stepMsg,
            msg=message,
        )

        if warning:
            message = "\033[93m" + message + "\033[0m"

        console_msg = "\033[90m[{tm}]\033[0m({tmr}) \033[1m{name:^15}\033[0m \033[92m[{step:^14}]\033[0m: {msg}".format(
            tm=strftime("%H:%M:%S"),
            tmr=self.txtTimer,
            name=self.name,
            step=self.stepMsg,
            msg=message,
        )

        log_file = open(self.log_path, "a")
        log_file.write(file_msg)
        log_file.close()

        if console or self.alwaysConsole:
            print(console_msg)

        return

    def stepUpdate(self, message):
        """
        Update the process step in logger
        """

        self.stepMsg = str(message)
        self.message("--process started", console=True)
        self.steps.append(message)

        return

    def beginTest(self):
        """
        Start a timed test. In a timed test, all messages sent to logger are sent to stdout
        """
        self.TestTimer = time()
        self.alwaysConsole = True
        self.message("begin test", warning=True)
        return

    def stopTest(self):
        """
        Stop a timed test and send result to logger
        """
        try:
            timer = time() - self.TestTimer
            self.message("end test: " + str(timer) + "sec", warning=True)
            self.alwaysConsole = False
        except:
            pass
        return

    def resetTest(self):
        """
        Reset a timed test. Equivalent to:
        logger.stopTest()
        logger.beginTest()
        """
        self.stopTest()
        self.beginTest()
        return
