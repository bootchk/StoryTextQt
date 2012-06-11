
"""
Adapt storytext to Qt
"""

# import logging
import traceback

# Generic (over toolkits) storytext
import storytext.guishared # , storytext.replayer

# Qt specialized submodules (similar to implementations for other GUI TK's.)
import widgetadapter
import describer
# interception modules
# import treeviewextract
import simulator

# For now, unique to Qt adaption
from idleHandlerSet import HandlerSet


from PySide.QtCore import QCoreApplication

# from ordereddict import OrderedDict

# modules that intercept widget factory
interceptionModules = [ simulator ] ## , treeviewextract ]


PRIORITY_STORYTEXT_IDLE = describer.PRIORITY_STORYTEXT_IDLE


class QtScriptEngine(storytext.guishared.ScriptEngine):
  
    eventTypes = simulator.eventTypes
    
    '''
    map happeningName to a displayable description.
    Accessed by guishared.getDisplayName().
    happeningName must correspond to row in simulator.eventTypes.
    '''
    signalDescs = {
        "closeEvent": "window closed",
        "clicked"   : "button clicked",
        "mouseMoveEvent"  : "mouse moved"
        }
    # "destroyed" : "window destroyed",
    columnSignalDescs = {
        "toggled.true": "checked box in column",
        "toggled.false": "unchecked box in column",
        "edited": "edited cell in column",
        "clicked": "clicked column header"
        }
    
    
    def __init__(self, universalLogging=True, **kw):
        print "Qt ScriptEngine init"
        # self.logger = logging.getLogger("qt engine")
        storytext.guishared.ScriptEngine.__init__(self, universalLogging=universalLogging, **kw)
        describer.setMonitoring(universalLogging)
        if self.uiMap or describer.isEnabled():
            self.performInterceptions()
        print "Qt ScriptEngine init returns"
    
    
    def setSUTReady(self):
      ''' 
      Called by SUT (harnessed) after event loop created. 
      
      Here we do things that depend on existence of event loop
      (some Qt methods depend, few GTK methods depend.)
      '''
      print "SE.setSUTReady"
      self.replayer.handlers.captureApplicationAndStartDelayedIdleHandlers()
      self.uiMap.doSUTReady()
      
      
    def createUIMap(self, uiMapFiles):
        if uiMapFiles:
            return simulator.UIMap(self, uiMapFiles)
        
        
    def addUiMapFiles(self, uiMapFiles):
        if self.uiMap:
            self.uiMap.readFiles(uiMapFiles)
        else:
            self.uiMap = simulator.UIMap(self, uiMapFiles)
        if self.replayer:
            self.replayer.addUiMap(self.uiMap)
        if not describer.isEnabled():
            self.performInterceptions()

    def performInterceptions(self):
        print "Qt ScriptEngine performInterceptions"
        eventTypeReplacements = {}
        for mod in interceptionModules:
            eventTypeReplacements.update(mod.performInterceptions())
        for index, (widgetClass, currEventClasses) in enumerate(self.eventTypes):
            if widgetClass in eventTypeReplacements:
                self.eventTypes[index] = eventTypeReplacements[widgetClass], currEventClasses
    
    
    def createReplayer(self, universalLogging=False):
        print "createReplayer"
        return UseCaseReplayer(self.uiMap, universalLogging, self.recorder)
                                
    def _createSignalEvent(self, eventName, signalName, widget, argumentParseData):
        print "_createSignalEvent", eventName, signalName # , widget
        stdSignalName = signalName.replace("_", "-")
        '''
        lkk ??? I don't understand why iterate over classes.
        It seems to me that each row in simulator.eventTypes is a possible event for a class,
        but we don't need to iterate over over all rows that the widget is a class of,
        we just need the one row whose class matches the widget class and whose signalName matches passed signalName.
        '''
        eventClasses = self.findEventClassesFor(widget) + simulator.universalEventClasses
        # print "Event classes for widget", eventClasses
        for eventClass in eventClasses:
            if eventClass.canHandleEvent(widget, stdSignalName, argumentParseData):
                return eventClass(eventName, widget, argumentParseData)
        
        """
        print "FallbackEventClass for happening", stdSignalName
        # lkk Why???
        if simulator.fallbackEventClass.widgetHasHappeningSignature(widget, stdSignalName):
            return simulator.fallbackEventClass(eventName, widget, stdSignalName)
        """
        '''
        lkk If we get here, it is not a programming error,
        since simulator.eventTypes is just a spec of (widgetClass, event) pairs that storytext
        is equipped to handle, but in some toolkits, event handlers  are optional?
        For this Qt adaptor, all rows in simulator.eventTypes should succeed?
        '''
        print "Programming error? _createSignalEvent returns None", eventClass

    def getDescriptionInfo(self):
        return "PyGTK", "gtk", "signals", "http://library.gnome.org/devel/pygtk/stable/class-gtk"

    def addSignals(self, classes, widgetClass, currEventClasses, module):
        print "addSignals"
        try:
            widget = widgetadapter.WidgetAdapter(widgetClass())
        except:
            widget = None
        signalNames = set()
        for eventClass in currEventClasses:
            try:
                className = self.getClassName(eventClass.getClassWithSignal(), module)
                classes[className] = [ eventClass.signalName ]
            except:
                if widget:
                    signalNames.add(eventClass.getAssociatedSignal(widget))
                else:
                    signalNames.add(eventClass.signalName)
        className = self.getClassName(widgetClass, module)
        classes[className] = sorted(signalNames)

    def getSupportedLogWidgets(self):
        print "getSupported"
        return describer.Describer.supportedWidgets



    
    
    
# Use Qt idle handlers instead of a separate thread for replay execution
class UseCaseReplayer(storytext.guishared.IdleHandlerUseCaseReplayer):
    def __init__(self, *args):
        print "Qt UCR init"

        self.handlers = HandlerSet()
        
        self.startedIdleDescriber = False  # Counter to prevent describing twice?
        
        # Call to super will call self and thus must follow create self.handlers.
        # super(UseCaseReplayer, self).__init__(*args)  # if inherits new-style class object
        storytext.guishared.IdleHandlerUseCaseReplayer.__init__(self, *args)
        
        
        """
        # Anyone calling events_pending doesn't mean to include our logging events
        # so we intercept it and return the right answer for them...
        self.interceptEventsPendingMethod()
        """
    
    def addUiMap(self, uiMap):
        self.uiMap = uiMap
        if not self.loggerActive:
            self.tryAddDescribeHandler()
    
    '''
    lkk Reimplement to fix app shutdown problems
    This is called:
    1) when a usecase is at EOF
    AND there are no more usecases
    2) when a recorder is active
    etc. (I don't really understand the complex state when this is called.)
    
    Also, the generic code in guishared is gtk specific and doesn't remove the replayer idleHandler,
    only sets the local self.idleHandler = None (and the idleHandler stops later when it gets
    the return value of False.)
    
    For our purpose, insure the replayer idleHandler is stopped and don't start the describeHandle
    if the app is trying to quit.
    '''
    """
    The problem with app shutdown was fixed by adding app.quit() to SUT.
    The problem was that automatic shutdown on last window closed did not shutdown app.
    Possibly because still timers in the event loop?
    Anyway, the solution of calling app.quit on main window close in the SUT
    allows the default implementation of tryAddDescribeHandler to work.
    We don't need what follows, which was an attempt to make sure there are no timers left in the event loop.
    
    I leave this cruft here because I still don't understand why the describeHandler is reinstalled
    and if it is preventing automatic app shutdown on last window close.
    
    def tryAddDescribeHandler(self):
        print "Qt reimplemented qtAdaptor.UseCaseReplayer.tryAddDescribeHandler"
        # Stop the replayer idleHandler
        self.handlers.stopAnyTimers()
        
        '''
        TODO: under what conditions should a describeHandler be started?
        '''
        
        # This is not right because it doesn't record any usecases on startup.
        # if self.readingEnabled:
        if not self.startedIdleDescriber:
        # if self.isMonitoring():
            self.makeDescribeHandler(self.handleNewWindows)
            self.startedIdleDescriber = True  # So won't start a second time
    """    

            
    def makeDescribeHandler(self, method):
        #print "makeDescribeHandler with method", method
        #traceback.print_stack() # debugging
        self.logger.debug("makeDescribeHandler")
        return self.handlers.idleAdd(method, priority=describer.PRIORITY_STORYTEXT_IDLE)
      
    """
    All shortcut stuff excised.
    
    In gtktoolkit, this was called from the shortcut stuff
    
    def tryRemoveDescribeHandler(self):
        print "tryRemoveDescribeHandler"
        if not self.isMonitoring() and not self.readingEnabled: # pragma: no cover - cannot test code with replayer disabled
            self.logger.debug("Disabling all idle handlers")
            self._disableIdleHandlers() # inherited from guishared, calls self.removeHandler
            if self.uiMap:
                self.uiMap.windows = [] # So we regenerate everything next time around
    """
    
    """
    TODO:
    
    def interceptEventsPendingMethod(self):
      self.orig_events_pending = gtk.events_pending
      gtk.events_pending = self.events_pending
    
    def events_pending(self): # pragma: no cover - cannot test code with replayer disabled
        if not self.isActive():
            self.logger.debug("Removing idle handler for descriptions")
            self._disableIdleHandlers()
        return_value = self.orig_events_pending()
        if not self.isActive():
            if self.readingEnabled:
                self.enableReplayHandler()
            else:
                self.logger.debug("Re-adding idle handler for descriptions")
                self.tryAddDescribeHandler()
        return return_value
    
    cruft?
    
    def makeTimeoutReplayHandler(self, method, milliseconds):
        return self.timeoutAdd(time=milliseconds, method=method, priority=describer.PRIORITY_STORYTEXT_REPLAY_IDLE)
    """
    
    def makeIdleReplayHandler(self, method):
        return self.handlers.idleAdd(method, priority=describer.PRIORITY_STORYTEXT_REPLAY_IDLE)

    def shouldMonitorWindow(self, window):
        """
        hint = window.get_type_hint()
        if hint == gtk.gdk.WINDOW_TYPE_HINT_TOOLTIP or hint == gtk.gdk.WINDOW_TYPE_HINT_COMBO:
            return False
        elif isinstance(window.child, gtk.Menu) and isinstance(window.child.get_attach_widget(), gtk.ComboBox):
            return False
        else:
            return True
        """
        # TODO Qt
        return True


    def findWindowsForMonitoring(self):
        # print "findWindowsForMonitoring"
        return filter(self.shouldMonitorWindow, QCoreApplication.instance().topLevelWidgets())


    def describeNewWindow(self, window):
        # print "describeNewWindow", window
        assert window is not None
        if window.isVisible():
            describer.describeNewWindow(window)


    def callReplayHandlerAgain(self):
        '''
        Boolean result of replayIdleHandler.
        
        For GTK:
        - True causes the handler to continue, i.e. get called again next iteration of event loop.
        - False is the opposite, i.e. stops the idle handler.
        
        For Qt this is moot (but function must be implemented, its pure virtual in the base class?)
        However, see elsewhere for how Qt handlers are stopped.
        '''
        return True
    
    
    """
    gtk cruft
    def runMainLoopWithReplay(self):
        print "runMainLoopWithReplay"
        while gtk.events_pending():
            gtk.main_iteration()
        if self.delay:
            time.sleep(self.delay)
        if self.isActive():
            self.describeAndRun()
    """
