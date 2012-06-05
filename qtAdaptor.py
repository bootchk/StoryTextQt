
"""
Adapt storytext to Qt
"""

# import os
# import logging
# from threading import Timer
# import signal

# Generic (over toolkits) storytext
import storytext.guishared # , storytext.replayer

# Qt special submodules
import widgetadapter
import describer
# interception modules
# import treeviewextract
import simulator



from PySide.QtCore import QObject, QAbstractEventDispatcher, QCoreApplication

# from ordereddict import OrderedDict

# modules that intercept widget factory
interceptionModules = [ simulator ] ## , treeviewextract ]


PRIORITY_STORYTEXT_IDLE = describer.PRIORITY_STORYTEXT_IDLE


class QtScriptEngine(storytext.guishared.ScriptEngine):
  
    eventTypes = simulator.eventTypes
    
    '''
    map happeningName to displayable description.
    Accessed by guishared.getDisplayName().
    happeningName must correspond to row in simulator.eventTypes.
    '''
    signalDescs = {
        "destroyed" : "window destroyed",
        "closeEvent": "window closed",
        "clicked"   : "button clicked",
        }
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
      self.replayer.handlers.captureApplication()
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
        for eventClass in eventClasses:
            if eventClass.canHandleEvent(widget, stdSignalName, argumentParseData):
                return eventClass(eventName, widget, argumentParseData)
          
        if simulator.fallbackEventClass.widgetHasSignal(widget, stdSignalName):
            return simulator.fallbackEventClass(eventName, widget, stdSignalName)
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



class HandlerSet(QObject):
  '''
  A set of event loop handlers (timers.)
  
  Responsibility:
  - know event loop
  - add and delete handlers
  - dispatch timer expirations (timeouts)
  Stereotype: Coordinator
  
  Specialized for Qt.
  Inherits QObject, which implements timers in Qt.
  '''
  def __init__(self):
    super(HandlerSet, self).__init__()
    self.handlers = {}  # map id to method
    self.eventLoop = None

    """
    This doesn't work yet because Storytext messes the signal?
    # Set alarm signal handler and a 10-second alarm
    signal.signal(signal.SIGALRM, self.captureApplication)
    signal.alarm(10)
    """
    """
    This doesn't work.  Because it is a separate thread from the app?
    # Start a Python timer to later capture the event loop
    timer = Timer(20, self.captureApplication)
    timer.start()
    """
    
  
  def captureApplication(self):
    ''' Capture the SUT event loop and install delayed handlers. '''
    # Get Qt event loop. Available before QApplication is created via classmethod on QAED
    self.eventLoop = QAbstractEventDispatcher.instance()
    if self.eventLoop is None or self.eventLoop == 0:
      # logger not exist?
      # self.logger.debug("No event loop yet?")
      print "No event loop yet?"
    else:
      print "Captured event loop"
      assert self.needIdle is not None
      # Install delayed idle handler
      timerID = self._idleAdd(self.needIdle)
      # Hack: put it in super (guishared) 
      self.idleHandler = timerID
    
    
  def idleAdd(self, method, priority):
    ''' 
    Add handler to be called each iteration of event loop.
    
    Differs from other GUI TK's: delays adding idle handler until later if no event loop.
    
    Implementation in Qt is a timer with time=0.
    Call methods of inherited QObject.
    '''
    # print "idleAdd", method
    if self.eventLoop is None:
      # print "Delaying"
      self.needIdle = method
      return None
    else:
      return self._idleAdd(method)
   
  
  def _idleAdd(self, method):
    ''' 
    Add idle handler.
    
    Precondition: event loop exists so can create timers on it.
    '''
    timerID = self.startTimer(0) # Zero means every iteration of event loop
    if timerID == 0:
      raise RuntimeError, "Could not start timer, no event loop?"
    else:
      self.handlers[timerID]=method
    return timerID
   
   
  def timeoutAdd(self, time, method, priority):
    print "timeoutAdd"
    return
  
  
  def removeHandler(self, handler):
    ''' 
    Remove (kill) a handler.
    Note there may be race conditions.
    '''
    self.killTimer (handler)
    del self.handlers[handler]
    
    
  def timerEvent(self, event):
    ''' 
    Callback for timer expired. Dispatch on ID. 
    In Qt, timer is periodic, continues to run.
    '''
    # print "dispatch timerEvent"
    self.handlers[event.timerId()]()  # method call
    
    
    
# Use Qt idle handlers instead of a separate thread for replay execution
class UseCaseReplayer(storytext.guishared.IdleHandlerUseCaseReplayer):
    def __init__(self, *args):
        print "Qt UCR init"

        self.handlers = HandlerSet()
        
        # Call to super will call self and thus must follow create self.handlers.
        # super(UseCaseReplayer, self).__init__(*args)  # if inherits new-style class object
        storytext.guishared.IdleHandlerUseCaseReplayer.__init__(self, *args)
        
        """
        # Anyone calling events_pending doesn't mean to include our logging events
        # so we intercept it and return the right answer for them...
        self.orig_events_pending = gtk.events_pending
        gtk.events_pending = self.events_pending
        """
    
    def addUiMap(self, uiMap):
        self.uiMap = uiMap
        if not self.loggerActive:
            self.tryAddDescribeHandler()
        
    def makeDescribeHandler(self, method):
        print "makeDescribeHandler"
        self.logger.debug("makeDescribeHandler")
        return self.handlers.idleAdd(method, priority=describer.PRIORITY_STORYTEXT_IDLE)
            
    def tryRemoveDescribeHandler(self):
        if not self.isMonitoring() and not self.readingEnabled: # pragma: no cover - cannot test code with replayer disabled
            self.logger.debug("Disabling all idle handlers")
            self._disableIdleHandlers() # inherited from guishared, calls self.removeHandler
            if self.uiMap:
                self.uiMap.windows = [] # So we regenerate everything next time around

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

    

    def makeTimeoutReplayHandler(self, method, milliseconds):
        return self.timeoutAdd(time=milliseconds, method=method, priority=describer.PRIORITY_STORYTEXT_REPLAY_IDLE)

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
        return True # GTK's way of saying the handle should come again

    def runMainLoopWithReplay(self):
        print "runMainLoopWithReplay"
        while gtk.events_pending():
            gtk.main_iteration()
        if self.delay:
            time.sleep(self.delay)
        if self.isActive():
            self.describeAndRun()
