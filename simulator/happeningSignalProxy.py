

from happeningProxy import QtHappeningProxy

from PySide.QtCore import Slot # QObject, SIGNAL, 


'''
Qt Signals

Emitting Signals
================
In Qt a signal LOOKS like a method, for example is often documented as "signal()". 
C++: the "emit" keyword in front of a call "emit signal()" is apparently syntactic sugar.
PySide: "Instance.Signal.emit()"
A signal in PyQt and PySide is NOT callable.

Generating Signals
==================
In Qt, a widget emits a signal AFTER a user action on a widget is handled by the widget.
To make the action happen in the SUT at replay time (to generate)
it is not enough to emit the signal (by calling widgetInstance.signal.emit() ).
Instead, a corresponding method must be called on the widget.
Said corresponding method does the handling (which may be customized) and then emits the signal.
Said corresponding method is often similarly named as the emitted signal.
E.G. QAbstractButton.click() generates the clicked() signal.

This is the reverse of GTK,
where sending a signal TO a widget causes it to handle a user action (external events)
and then possibly emit other signals.

In Qt, an app programmer usually only directly emits custom signals.
Even in the storytext meta program, there is little need to directly emit signals to the SUT???

Signal Arguments
================
In Qt, most signals have no optional arguments (is agnostic, flexible).
(Unlike GTK, where an Event() instance is usually passed.)
A rare exception is valueChanged().
But also see signal mapping stuff for sets of buttons.

A signal is emitted to all subscribers (receivers).
Signals are emitted to recievers in the order connected.
Signals are rarely blocked (however see QObject.blockSignals().)
A signal is emitted from instance to instance.
Receivers can query sender().

Connections
===========
A connection is between instances.
Internally, connections are stored as metadata by Qt runtime system.


'''


  
def connectSignal(signalName, handlerMethod, sender):
  ''' 
  Subscribe to signalName of widget sender with handler given by handlerMethod. 
  Return ID of connection.
  
  !!! Note Qt doesn't allow optional args to be be passed and fixed at connect time.
  TODO: move this to widgetAdapter
  '''
  # GTK:
  # handler = gobj.connect(self.getRecordSignal(), method, self)
  # Qt: Old syntax: not correct?: QObject.connect(sender, SIGNAL(signalName), method)
  print "connectSignal>>>>>>>>>>>>>", signalName
  result = eval( "sender." + signalName + ".connect(handlerMethod)")
  if not result:
    raise RuntimeError, "Storytext failed to connect signal:" + signalName
  




   

class SignalEvent(QtHappeningProxy):
    '''
    Base class for Qt signals.
    
    In Qt, all signals are intra-application.
    (Possibly some come from network managers?)
    '''
    def __init__(self, name, widget, signalName=None):
        QtHappeningProxy.__init__(self, name, widget)
        if signalName:
            self.signalName = signalName
        else:
            self.signalName = self.getAssociatedSignal(widget)


    """
    TODO GTK specialized getAssociatedSignal as follows:
    
    elif widget.isInstanceOf(gtk.Button) or widget.isInstanceOf(gtk.ToolButton):
        return "clicked"
    elif widget.isInstanceOf(gtk.Entry):
        return "activate"
    """
    
    @classmethod
    def widgetHasHappeningSignature(cls, widgetAdaptor, happeningName):
        '''
        Does widget have the signature of happeningName?
        This specializes a pure virtual method of ABC to: Qt signals
        '''
        """ GTK cruft needed???
        if widget.isInstanceOf(gtk.TreeView):
            # Ignore this for treeviews: as they have no title/label they can't really get confused with other stuff
            return widget.get_model() is not None
        else:
            return gobject.signal_lookup(signalName, widget.widget) != 0
        """
        return widgetAdaptor.canWidgetEmitSignal(happeningName)
      

    def interceptHappeningToRecorder(self, communicantWidget, interceptMethod):
        '''
        Connect a signal from communicantWidget to interceptMethod, which is usually the recorder?
        
        A widget (*communicantWidget*, which is self.widget.widget) sent *signal* (retrieved by self.getRecordSignal())
        which this GtkEvent represents.
        Leave all SUT handlers in place, but also connect *interceptMethod* to signal
        (after existing SUT handlers in the chain of handlers, but before the default handler.)
        ??? Qt has no default handler.
        ??? *interceptMethod* is always recorder.writeEvent ???
        
        It has already been arranged to intercept TK methods that change the handler chain (stop_emission, destroy, etc.).
        Those interceptions set flags when called, indicating postponed actions.
        Also arrange a signal handler to execute said postponed actions of original signal handler,
        AFTER recorder.method has received signal.
        
        Note this depends on signal handlers being executed in the order they are connected, which is true for Qt and GTK.
        '''
        # print "connectRecord to handler:", interceptMethod
        signalName = self.getRecordSignal()
        # Arrange for recorder to handle signal, via intermediary; remember interceptMethod in instance var
        assert self.recorderHandler is None
        self.recorderHandler = interceptMethod
        connectionID = connectSignal(signalName=signalName, 
                                handlerMethod=self._signalIntermediary, 
                                sender=communicantWidget)
        """
        # Arrange for self.executePostponedActions to handle signal LAST
        connectSignal(signalName=signalName, 
                      interceptMethod=self.executePostponedActions, 
                      sender=sender)
        """
        return connectionID # Caller wants ID of first signal handler if we connected more than one.


    @Slot()
    def _signalIntermediary(self):
      '''
      A Qt slot (handler, callback) for self's signal, 
      that simply redirects to self.recorderHandler, passing self as parameter.
      
      This is necessary since Qt does not allow optional args in a call to connect().
      This intermediary simply passes self as parameter of redirected call to recorder.
      '''
      assert self.recorderHandler is not None
      self.recorderHandler(self)  # invoke with parameter: singleton? instance of this class
      
      
    def getChangeMethod(self):
        ''' 
        Return widget's method that causes widget to (eventually) send self's signal.
        
        In Qt, each widget has a different named method that (eventually) causes signal to emit.
        See discussion above.
        Possibly QMetaObject.activate() will send a signal but it is private.
        (In GTK:,every widget is a gobject that can emit(signalName))
        '''
        assert self.__class__.widgetSignalCorrespondingMethodName is not None
        # Return function object of corresponding method
        result = eval( "self.widget." + self.__class__.widgetSignalCorrespondingMethodName)
        # print "getChangeMethod returns:", result
        return result


    def getGenerationArguments(self, argumentString):
        ''' 
        Get args for method to generate signal.
        
        This method is virtual in base class, must be reimplemented here (in subclass.)
        
        Qt: method is a corresponding method of widget, args vary but usually None.
        ( GTK: method is emit(), need standard args for emit.)
        '''
        return []


    def getEmissionArgs(self, argumentString):
        return []







class ClickedSignal(SignalEvent):
    '''
    Qt signal "clicked" from a QAbstractButton or descendant.
    
    In Qt, pointer (mouse input device) button events are handled by widget callbacks
    (including propagation to parents)
    but by default (unless reimplemented) result in the clicked signal, 
    for widgets derived from QAbstractButton.
    '''
  
    signalName = "clicked" # See Qt docs whether is for press or release
    widgetSignalCorrespondingMethodName = "click"
    # eventType = gtk.gdk.BUTTON_RELEASE

    """
    
    """
    """
    For now, not reimplemented for Qt, use super which returns empty arg list.
    
    def getEmissionArgs(self, argumentString):
        area = self.getAreaToClick(argumentString)
        event = gtk.gdk.Event(self.eventType)
        event.x = float(area.x) + float(area.width) / 2
        event.y = float(area.y) + float(area.height) / 2
        event.button = self.buttonNumber
        return [ event ]

    def getAreaToClick(self, *args):
        return self.widget.get_allocation()
    """
      
"""
class ClickEvent(SignalEvent):
    def shouldRecord(self, widget, event, *args):
        return SignalEvent.shouldRecord(self, widget, event, *args) and event.button == self.buttonNumber

    def getEmissionArgs(self, argumentString):
        area = self.getAreaToClick(argumentString)
        event = gtk.gdk.Event(self.eventType)
        event.x = float(area.x) + float(area.width) / 2
        event.y = float(area.y) + float(area.height) / 2
        event.button = self.buttonNumber
        return [ event ]

    def getAreaToClick(self, *args):
        return self.widget.get_allocation()
"""

"""
class LeftClickEvent(ClickEvent):
    signalName = "button-release-event" # Usually when left-clicking things (like buttons) what matters is releasing
    buttonNumber = 1
    eventType = gtk.gdk.BUTTON_RELEASE

class RightClickEvent(ClickEvent):
    signalName = "button-press-event"
    buttonNumber = 3
    eventType = gtk.gdk.BUTTON_PRESS
"""


# Some widgets have state. We note every change but allow consecutive changes to
# overwrite each other. 
# lkk Most subclasses in miscevents.py
class StateChangeEvent(QtHappeningProxy):
    signalName = "changed"
    def isStateChange(self):
        return True
    def shouldRecord(self, *args):
        return QtHappeningProxy.shouldRecord(self, *args) and self.eventIsRelevant()
    def eventIsRelevant(self):
        return True
    def getGenerationArguments(self, argumentString):
        return [ self.getStateChangeArgument(argumentString) ]
    def getStateChangeArgument(self, argumentString):
        return argumentString
    def _outputForScript(self, *args):
        return self.name + " " + self.getStateDescription(*args)