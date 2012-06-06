
""" 
Events for Qt Windows of various types, including dialogs 

Window closing happening sequence:
=================================
- window manager calls closeEvent() method of window
- closeEvent handler saves user's data and returns
- closeEvent handler optionally calls hide() method of window
- OR closeEvent handler optionally(!) calls destroy() method of window (a closed window is not automatically destroyed.)
-- destroy() method emits destroyed() signal

Distinguish:          thing from user           AND     thing from TK
Qt thing/handler:     QCloseEvent/closeEvent()        "destroyed" signal/*any connected slot*
GTK signal:           "delete-event"                  "destroy"

Thing from user is via window manager and is a command to close a window, arriving before the window is closed.
Thing from TK is intra-application signal from the TK arriving after window has been destroyed.
"""

from happeningSignalProxy import SignalEvent
from happeningEventProxy import QtEventProxy

from PySide.QtCore import QEvent


class CloseEvent(QtEventProxy):
    '''
    GUIEvent for the low-level event from window manager to window meaning "user says close window".
    It means to the app: the window is about to be destroyed.
    (Rarely used: Windows can also be closed programatically by calling close() method
    which (?) engenders "destroyed()" signal?)
    '''
    # lkk Is name of event handler method, not a signal.
    signalName = "closeEvent"
    eventQtType = QEvent.Close



class DestroySignal(SignalEvent):
    ''' 
    Happening signal from window when window is closed (sic).
    '''
  
    # QT "closeEvent" is a low-level event from window manager, here need high-level signal
    # GTK "delete-event"
    signalName = "destroyed"  
    widgetSignalCorrespondingMethodName = "destroy"
    
    
    """
    lkk I don't think we need this reimplement for Qt.
    def generate(self, argumentString):
        SignalEvent.generate(self, argumentString)    
        self.disableIntercepts(self.widget)
        self.widget.destroy() # just in case...
    """

    def shouldRecord(self, *args):
        ''' Reimplement so we still record closing of hidden windows. '''
        return True



# GTK cruft
"""
class ResponseEvent(SignalEvent):
    signalName = "response"
    
    def getStandardResponses():
        info = {}
        for name in dir(gtk):
            # RESPONSE_NONE is meant to be like None and shouldn't be recorded (at least not like this)
            if name.startswith("RESPONSE_") and name != "RESPONSE_NONE":
                info[getattr(gtk, name)] = name.lower().replace("_", ".", 1)
        return info
        

    dialogInfo = {}
    standardResponseInfo = getStandardResponses()

    def __init__(self, name, widget, responseId):
        SignalEvent.__init__(self, name, widget)
        self.responseId = self.parseId(responseId)
            
    def shouldRecord(self, widget, responseId, *args):
        return self.responseId == responseId and \
               SignalEvent.shouldRecord(self, widget, responseId, *args)

    @classmethod
    def getAllResponses(cls, dialog, widgetAdapter):
        responses = []
        respId = dialog.get_response_for_widget(widgetAdapter.widget)
        if respId in cls.standardResponseInfo:
            responses.append(cls.standardResponseInfo[respId])
        elif respId != gtk.RESPONSE_NONE:
            responses.append("response." + widgetAdapter.getUIMapIdentifier().replace("=", "--"))
        for child in widgetAdapter.getChildren():
            responses += cls.getAllResponses(dialog, child)

        return responses

    @classmethod
    def getAssociatedSignatures(cls, widget):
        return cls.getAllResponses(widget, WidgetAdapter.adapt(widget.action_area))

    @classmethod
    def storeApplicationConnect(cls, dialog, signalName, *args):
        currDialogInfo = cls.dialogInfo.setdefault(dialog, [])
        currDialogInfo.append((signalName, args))
        return len(currDialogInfo) - 1

    def getProgrammaticChangeMethods(self):
        return [ self.widget.response ]

    def _connectRecord(self, dialog, method):
        # If it doesn't have this patched-on attribute, it's a dialog which existed before we enabled StoryText
        # (we're probably therefore recording a shortcut). Can't record anything sensible, so don't do anything
        if hasattr(dialog, "connect_for_real"):
            handler = dialog.connect_for_real(self.getRecordSignal(), method, self)
            dialog.connect_for_real(self.getRecordSignal(), self.executePostponedActions)
            return handler            

    @classmethod
    def connectStored(cls, dialog):
        # Finally, add in all the application's handlers
        for signalName, args in cls.dialogInfo.get(dialog, []):
            dialog.connect_and_store(signalName, *args)

    def getEmissionArgs(self, argumentString):
        return [ self.responseId ]

    def findChildWidget(self, widgetAdapter, identifier):
        for child in widgetAdapter.getChildren():
            if identifier in child.findPossibleUIMapIdentifiers():
                return self.widget.get_response_for_widget(child.widget)

    def parseId(self, responseId):
        # May have to reverse the procedure in getResponseIdSignature
        if "--" in responseId:
            return self.findChildWidget(WidgetAdapter.adapt(self.widget.action_area), responseId.replace("--", "=")) 
        else:                
            return getattr(gtk, "RESPONSE_" + responseId.upper())
"""