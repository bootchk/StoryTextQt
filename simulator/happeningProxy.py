

from storytext.guishared import GuiEvent, MethodIntercept
from storytext.definitions import UseCaseScriptError


'''
Adapt Qt

Signals Versus Events
=====================
Qt distinguishes events and signals.
(Unlike GTK where the toolkit converts external events to signals.)
For storytext purposes, they are both "GUIEvents", or "happenings."
A GUIEvent is a proxy, a base class representing either low-level (QEvent) or high-level (Qt Signal).

'''

class QtHappeningProxy(GuiEvent):
    '''
    Abstract Base Class for proxy for Qt happenings.
    Happening is an abstraction of (signals, events).
    
    Stereotype: Proxy: stand-in for the real thing.
    
    Responsibility:
    Know:
    - info to reconstruct a real happening
    - changeMethod to receive real happening
        
    Subclasses: 
    - event happening (QEvent, from external input devices and window manager.) 
    - signal happening (QSignal, intra-application.)
    '''
  
    def __init__(self, name, widget, *args):
        GuiEvent.__init__(self, name, widget)
        ''' Intercept methods that affect storytext snooping. '''
        # self.interceptMethod(getWidgetPropagationStopMethod(widget), EmissionStopIntercept)
        """
        Why?  Something about storytext is a default handler and not getting signals unless we intercept stop??
        I don't think this pertains to Qt: no way to stop a signal in Qt.
        # stop_emission() method on gobject (super of widget.)
        self.interceptMethod(self.widget.stop_emission, EmissionStopIntercept)
        # emit_stop_by_name() method on widget
        self.interceptMethod(self.widget.emit_stop_by_name, EmissionStopIntercept)
        self.interceptMethod(self.widget.get_toplevel().destroy, DestroyIntercept)
        """
        self.stopEmissionMethod = None
        self.destroyMethod = None
        
        # recorder method to call when happening is intercepted
        self.recorderHandler = None
        
        # TODO: migrate to happeningSignalProxy
        # Name of widget's corresponding method to call to generate signal.
        self.widgetSignalCorrespondingMethodName = None
    
    '''
    lkk
    By reimplementing GuiEvent.interceptMethod(),
    prevent "NoneType has no attribute sendEvent" for getSelf(sendEvent()).
    I.E. sendEvent is a class method and has no self instance.
    We don't need to intercept any methods anyway???
    '''
    """
    def interceptMethod(self, method, interceptClass):
      pass
    """

    @staticmethod
    def disableIntercepts(window):
        if isinstance(window.destroy, MethodIntercept):
            window.destroy = window.destroy.method


    @classmethod
    def getAssociatedSignal(cls, widget):
        '''
        Get signature of the happening, where happening means low-level event or high-level signal.
        
        TODO: should refactor and rename to say "signature" : this is not a signal in the Qt sense.
        rename getAssociatedSignal to getAssociatedSignature everywhere (including in guishared
        rename signalName to signatureName everywhere
        '''
        if hasattr(cls, "signalName"):
            return cls.signalName


    @classmethod
    def canHandleEvent(cls, widget, happeningName, *args):
        '''
        Can widget handle (or emit) happeningName?
        
        Note storytext calls it an *event*, here we use *happening* to mean either QEvent or Qt Signal.
        '''
        # storytext signalProxy class has happeningName AND GUI widget class has happeningName (signal or handler method)
        result = cls.getAssociatedSignal(widget) == happeningName and cls.widgetHasHappeningSignature(widget, happeningName)
        """
        lkk ????? I'm still trying to decide if this is appropriate for Qt.
        if not result:
          '''
          lkk: A programming error in simulator.events .
          simulator.events declares "widget handles happening" but when we get here, that declaration is not corroborated.
          Conceivably, simulator.events could declare *possible* custom signals,
          in which case this is NOT a programming error.
          '''
          print "Widget", widget, "not handling happening", happeningName
        """
        return result

        
        
    def delayLevel(self):
        # If we get this when in dialog.run, the event that cause us has not yet been
        # recorded, so we should delay
        """
        GTK
        topLevel = self.widget.get_toplevel()
        return int(hasattr(topLevel, "dialogRunLevel") and topLevel.dialogRunLevel > 0)
        """
        return 0  # Qt temporary hack


    def getRecordSignal(self):
        return self.signalName


    def connectRecord(self, recorderMethod):
        ''' 
        Connect recorder to a happening.
        
        Subclasses may intercept before (event) or after (signal) the happening.
        
        Implementation: call a subclass recorderMethod.
        '''
        # assert the parameter "recorderMethod" is writeEvent() method of scriptEngine.recorder
        self.interceptHappeningToRecorder(communicantWidget=self.widget.widget, interceptMethod=recorderMethod)
      

    def outputForScript(self, widget, *args):
        return self._outputForScript(*args)

    """
    # Qt requires a slot for signal handlers
    @Slot()
    def executePostponedActions(self, *args):
        print "executePostponedActions"
        if self.stopEmissionMethod:
            self.stopEmissionMethod(self.getRecordSignal())
            self.stopEmissionMethod = None
        if self.destroyMethod:
            self.destroyMethod()
    """
    
    def shouldRecord(self, *args):
        ''' 
        Default is to only record happenings from visible widgets. 
        Subclasses may reimplement.
        '''
        return GuiEvent.shouldRecord(self, *args) and self.widgetVisible()

    def _outputForScript(self, *args):
        return self.name


    def widgetVisible(self):
        # Qt
        return self.widget.isVisible()

    def widgetSensitive(self):
        # Qt
        return self.widget.isEnabled()

    def describeWidget(self):
        # Qt
        return repr(self.widget.objectName())


    def generate(self, argumentString):
        '''
        Called at replay time to generate real happening (to SUT) corresponding to self.
        '''
        self.checkWidgetStatus()  # super
        
        '''
        Create args for call to changeMethod.
        In subclasses, creates QEvent for events, other args for signals
        '''
        args = self.getGenerationArguments(argumentString)  # subclass
        
        try:
            # Assert self.changeMethod is a function object, a bound method of a widget
            # print "Generate happening:", self.signalName
            self.changeMethod(*args)
        except TypeError:
            print self.changeMethod, args
            raise UseCaseScriptError, "Cannot generate happening " + repr(self.signalName) + \
                  " for  widget of type " + repr(self.widget.getType())

