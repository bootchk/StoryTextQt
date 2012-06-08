
from PySide.QtCore import QCoreApplication

def getAppInstance():
    ''' Qt: exists one QApplication instance, or None. '''
    return QCoreApplication.instance()