
""" Main entry point for simulator functionality """

from PySide.QtGui import QMainWindow, QDialog, QFileDialog, QAbstractButton, QGraphicsView
from PySide.QtCore import Slot

from applicationUnderTest import getAppInstance
import happeningSignalProxy
import graphicsviewevents
import windowevents
# , filechooserevents, treeviewevents, 
import miscevents

import storytext.guishared

performInterceptions = miscevents.performInterceptions
"""
origDialog = gtk.Dialog
origFileChooserDialog = gtk.FileChooserDialog    
"""
origDialog = QDialog
origFileChooserDialog = QFileDialog



'''
Signals from SUT to simulator, but not part of a use case.

The simulator wants a signal on SUT shutdown,
so storytext can interact with tester to map any events that are new to the map.
'''
  
def connectAppShutdownSignal(handler):
  ''' 
  Qt specific.
  
  Two candidate signals:
  - aboutToQuit()    Event loop finished: may come from system-wide shutdown
  - lastWindowClose()  User closed last window.
  
  GTK: gtk.quit_add(1, self.fileHandler.write) 
  Note this is not quite a signal in GTK, but a special case?
  '''
  getAppInstance().aboutToQuit.connect(handler)
  
  
  
  
  
  
class DialogHelper(object):
    ''' 
    Mixin class multiply inherited below. 
    For Qt, must derive from new-style object class.
    '''
    def tryMonitor(self):
        if self.uiMap.scriptEngine.recorderActive():
            self.connect_for_real = self.connect
            self.connect = self.store_connect
            self.disconnect_for_real = self.disconnect
            handlerAttrs = [ "disconnect", "handler_is_connected", "handler_disconnect",
                             "handler_block", "handler_unblock" ]
            for attrName in handlerAttrs:
                setattr(self, attrName, self.handlerWrap(attrName))
            
    def store_connect(self, signalName, *args):
        return windowevents.ResponseEvent.storeApplicationConnect(self, signalName, *args)

    def handlerWrap(self, attrName):
        method = getattr(self, attrName)
        def wrapped_handler(handler):
            return method(self.handlers[handler])
        return wrapped_handler

    def connect_and_store(self, signalName, method, *args):
        def wrapped_method(*methodargs, **kw):
            happeningSignalProxy.DestroyIntercept.inResponseHandler = True
            try:
                method(*methodargs, **kw)
            finally:
                happeningSignalProxy.DestroyIntercept.inResponseHandler = False
        self.handlers.append(self.connect_for_real(signalName, wrapped_method, *args))

"""
    def run(self):
        if gtk.main_level() == 0 or not hasattr(self, "connect_for_real"):
            # Dialog.run can be used instead of the mainloop, don't interfere then
            return origDialog.run(self)
        
        origModal = self.get_modal()
        self.set_modal(True)
        self.dialogRunLevel += 1
        self.uiMap.monitorAndStoreWindow(self)
        self.connect_for_real("response", self.runResponse)
        self.show_all()
        self.response_received = None
        while self.response_received is None:
            self.uiMap.scriptEngine.replayer.runMainLoopWithReplay()

        self.dialogRunLevel -= 1
        self.set_modal(origModal)
        happeningSignalProxy.GtkEvent.disableIntercepts(self)
        return self.response_received

    def runResponse(self, dialog, response):
        self.response_received = response
        

class Dialog(DialogHelper, origDialog):
    uiMap = None
    def __init__(self, *args, **kw):
        origDialog.__init__(self, *args, **kw)
        self.dialogRunLevel = 0
        self.handlers = []
        self.tryMonitor()
    

class FileChooserDialog(DialogHelper, origFileChooserDialog, object):
    uiMap = None
    def __init__(self, *args, **kw):
        origFileChooserDialog.__init__(self, *args, **kw)
        self.dialogRunLevel = 0
        self.handlers = []
        self.tryMonitor()
"""

class UIMap(storytext.guishared.UIMap):
    ignoreWidgetTypes = [ "Label" ]
    def __init__(self, *args): 
        storytext.guishared.UIMap.__init__(self, *args)
        """
        ??? Redirecting calls to gtk.Dialog to augmented Dialog class. ???
        gtk.Dialog = Dialog
        Dialog.uiMap = self
        gtk.FileChooserDialog = FileChooserDialog
        FileChooserDialog.uiMap = self
        """
        # Arrange to write changes to the GUI map when the application exits.
        # For Qt, this is done later
        
    
    def doSUTReady(self):
      ''' Do initialization that requires SUT event loop. '''
      # Arrange to write changes to the GUI map when the application exits
      print "UIMap.doSUTReady"
      connectAppShutdownSignal(self.handleSUTShutdown)
      
    @Slot()
    def handleSUTShutdown(self):
      ''' Event loop is empty. '''
      print "handleSUTShutdown"
      self.fileHandler.write()

    
    
    def monitorChildren(self, widget, *args, **kw):
        """
        if widget.getName() != "Shortcut bar" and \
               not widget.isInstanceOf(gtk.FileChooser) and not widget.isInstanceOf(gtk.ToolItem):
            storytext.guishared.UIMap.monitorChildren(self, widget, *args, **kw)
        """
        storytext.guishared.UIMap.monitorChildren(self, widget, *args, **kw)

    def monitorWindow(self, window):
        if window.isInstanceOf(origDialog):
            # Do the dialog contents before we do the dialog itself. This is important for FileChoosers
            # as they have things that use the dialog signals
            self.logger.debug("Monitoring children for dialog with title " + repr(window.getTitle()))
            self.monitorChildren(window, excludeWidgets=self.getResponseWidgets(window, window.action_area))
            self.monitorWidget(window)
            windowevents.ResponseEvent.connectStored(window)
        else:
            storytext.guishared.UIMap.monitorWindow(self, window)
"""
    def getResponseWidgets(self, dialog, widget):
        widgets = []
        for child in widget.get_children():
            if dialog.get_response_for_widget(child) != gtk.RESPONSE_NONE:
                widgets.append(child)
        return widgets
"""



'''
eventTypes is a table of configuration or specification.
It specifies what StoryText monitors.
See also customEventTypes.

A tuple here is a (widgetClass, happeningClass).
(actually specified as (widgetClass, [happeningClass,...]).

A tuple asserts a different thing depending on type of happening:
- widgetClass sends happeningSignalClass
- widgetClass receives happeningEventClass
(The meaning is different for gtk, where wdgetClass always RECEIVES happeningClass.)

!!! Keep the descriptions in sync in qtAdaptor.signalDescs
'''
eventTypes = [
        (QMainWindow,         [ windowevents.CloseEvent ]),
        (QAbstractButton,     [ happeningSignalProxy.ClickedSignal ]),
        (QGraphicsView,       [ graphicsviewevents.MouseMoveEvent]),
        ]
# windowevents.DestroySignal,
                                
"""
        (gtk.Button           , [ baseevents.SignalEvent ]),
        (gtk.ToolButton       , [ baseevents.SignalEvent ]),
        (gtk.MenuItem         , [ miscevents.MenuItemSignalEvent ]),
        (gtk.CheckMenuItem    , [ miscevents.MenuActivateEvent ]),
        (gtk.ToggleButton     , [ miscevents.ActivateEvent ]),
        (gtk.ToggleToolButton , [ miscevents.ActivateEvent ]),
        (gtk.ComboBoxEntry    , []), # just use the entry, don't pick up ComboBoxEvents
        (gtk.ComboBox         , [ miscevents.ComboBoxEvent ]),
        (gtk.Entry            , [ miscevents.EntryEvent, 
                                  baseevents.SignalEvent ]),
        (gtk.TextView         , [ miscevents.TextViewEvent ]),
        (gtk.FileChooser      , [ filechooserevents.FileChooserFileSelectEvent, 
                                  filechooserevents.FileChooserFolderChangeEvent, 
                                  filechooserevents.FileChooserEntryEvent ]),
        (gtk.Dialog           , [ windowevents.ResponseEvent, 
                                  windowevents.DeletionEvent ]),
        (gtk.Window           , [ windowevents.DeletionEvent ]),
        (gtk.Notebook         , [ miscevents.NotebookPageChangeEvent ]),
        (gtk.TreeView         , [ treeviewevents.RowActivationEvent, 
                                  treeviewevents.TreeSelectionEvent, 
                                  treeviewevents.RowExpandEvent, 
                                  treeviewevents.RowCollapseEvent, 
                                  treeviewevents.RowRightClickEvent, 
                                  treeviewevents.CellToggleEvent,
                                  treeviewevents.CellEditEvent, 
                                  treeviewevents.TreeColumnClickEvent ])
]
"""

universalEventClasses = [ ] ## GTK baseevents.LeftClickEvent, baseevents.RightClickEvent ]
# lkk ??? does this make sense to prefer one subclass for fallback?
fallbackEventClass = happeningSignalProxy.SignalEvent
