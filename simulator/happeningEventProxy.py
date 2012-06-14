

from storytext.guishared import GuiEvent

from ..eventFilter import StorytextQtEventFilter
from applicationUnderTest import getAppInstance
from happeningProxy import QtHappeningProxy


# Note we only import any Qt for assertions: this is ABC, subclasses specialize to Qt
from PySide.QtCore import QEvent


class QtEventProxy(QtHappeningProxy):
    '''
    Proxy for a (low-level) QEvent.
    
    QEvents are low-level, from outside the app.
    E.G. from a window manager (QCloseEvent)
    or from input devices such as a pointer/mouse (QEvent)
    QEvent is a base class with many subclasses.
    
    Qt delivers QEvents to callbacks, i.e. QWidget handler methods.
    QEvents are subject to propagation and accept(), ignore().
    But we use QEventFilters to intercept handlers
    (at the head of the propagation chain)
    so we don't need to worry about accept(), ignore().
    
    This is an abstract base class (not to be instantiated.)
    Subclasses must have static vars:
    - eventQtType whose value is the Qt enum value for type of the QEvent e.g. QEvent.Close
    - eventQtFactory whose value is the class (factory) for the QEvent (subclass) e.g. QCloseEvent
    '''
  
    def __init__(self, eventName, widget, *args):
        assert widget is not None
        GuiEvent.__init__(self, eventName, widget)
        self.recorderHandler = None

    
    # @staticmethod
    @classmethod
    def widgetHasHappeningSignature(cls, widgetAdaptor, happeningName):
        '''
        Does widget have the signature of happeningName?
        This specializes a pure virtual method of ABC to: Qt events
        '''
        return widgetAdaptor.canWidgetHandleEvent(happeningName)
      
      
    def interceptHappeningToRecorder(self, communicantWidget, interceptMethod):
        '''
        Connect (intercept) self event from GUI TK to handlerMethod, which is usually the recorder?
        
        A widget (self.getRealWidget()) receives low-level event (QEvent) which self GuiEvent represents.
        Make recorder intercept ahead of widget, by installing QEventFilter.
        '''
        self.recorderHandler = interceptMethod
        # Make the filter object a child of the communicantWidget?  Seems to work better than unparented.
        filterObj = StorytextQtEventFilter(parent=communicantWidget, 
                                           eventType=self.__class__.eventQtType, 
                                           interceptMethod=interceptMethod,
                                           interceptArgs=[self])
        #print filterObj
        # print self.getRealWidget()
        communicantWidget.installEventFilter(filterObj)
        # print "Installed event filter for event", self.signalName


    def getChangeMethod(self):
        ''' 
        Return a function object (callable) of the SUT that creates self's real event.
        
        Called by the replayer (reading from the DRIVING usecase.)
        Replayer then calls the changeMethod, which creates the event.
        Then an eventFilter intercepts the event and stores a copy in the RESULT usecase.
        (To be diffed with the DRIVING usecase.)
        Then SUT handles the event.
        
        In Qt, QCoreApplication.postEvent ( QObject * receiver, QEvent * event )
        
        NOT the widget's method that handles event. 
        In Qt, by convention, the handler has the same name as the event, except for capitalization.
        result = eval( "self.widget." + self.signalName)
        '''
        # During development, was a  problem with getSelf(postEvent)
        app = getAppInstance()
        result = app.postEvent
        
        """
        '''
        Alternative:
        Call the handler directly, bypassing event loop and eventFilter.
        Unfortunately, the standard usecase recording then fails, since it comes from the eventFilter.
        So we need to write to the usecase outside normal.
        '''
        result = eval( "self.widget." + self.signalName)
        """
        
        # print "getChangeMethod returns:", result
        return result


    
    '''
    Generation args if changeMethod is app.postEvent.
    If we were to call the SUT handler method, generation args would just be: return [event]
    '''
    def getGenerationArguments(self, argumentString):
        '''
        Return arguments for generating an event (for changeMethod, see above.)
        
        The changeMethod has an actual parameter that is an instance of a subclass of QEvent.
        
        !!! Note two uses of args: args to the factory which produces args to the changeMethod.
        '''
        # print "getGenerationArguments"
        receiver = self.getRealWidget()
        event = self.getRealEvent(argumentString)
        assert isinstance(event, QEvent)
        return [receiver, event]
    
    
    def getRealEvent(self, argumentString):
        '''
        Return real event corresponding to this proxy event.
        
        Call factory method with argumentString.
        argumentString is a serialization from the usecase file.
        
        For some QEvents, the factory has NO args,  e.g. QCloseEvent()
        This is the default implementation:
        the argumentString is not used because the factory has no args e.g. QCloseEvent().
        
        Subclasses should reimplement if the factory requires arguments.
        A reimplementation should produce actual args by parsing and deserializing argumentString.
        '''
        # print "argumentString", argumentString
        result = self.__class__.eventQtFactory()
        assert isinstance(result, QEvent)
        # print "realEvent", result, result.__class__
        return result
    
    
    '''
    This is reimplemented to avoid a problem in generic StoryText code
    (where it intercepts methods to avoid knock-on effects)
    The problem is that getSelf() tries but fails to intercept classmethod QCoreApplication.postEvent().
    getSelf() is supposed to find self (instance) of methods.
    Since this subverts generic StoryText interception to avoid knock-on effects,
    I'm not sure of the ramifications.
    '''
    def interceptMethod(self, method, interceptClass):
      pass