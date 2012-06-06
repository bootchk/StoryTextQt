

from storytext.guishared import GuiEvent

from ..eventFilter import StorytextQtEventFilter
from happeningProxy import QtHappeningProxy

from PySide.QtCore import QEvent
from PySide.QtGui import QCloseEvent




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
    '''
  
    # Subclasses must have static var eventQtType
  
    def __init__(self, eventName, widget, *args):
        GuiEvent.__init__(self, eventName, widget)
        self.recorderHandler = None
        # Type (an enum, not the class) of event in Qt
        # Should be a specific subclass of QEvent
        # TODO: hardcoded to QCloseEvent, should be parameter??
        self.eventQtType = QEvent.Close
    
    
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
        
        A widget (self.widget.widget) receives low-level event (QEvent) which self GuiEvent represents.
        Make recorder intercept ahead of widget, by installing QEventFilter.
        '''
        self.recorderHandler = interceptMethod
        # Make the filter object a child of the communicantWidget?  Seems to work better than unparented.
        filterObj = StorytextQtEventFilter(parent=communicantWidget, 
                                           eventType=self.__class__.eventQtType, 
                                           interceptMethod=interceptMethod,
                                           proxyEvent=self)
        #print filterObj
        # print self.widget.widget
        communicantWidget.installEventFilter(filterObj)
        print "Installed event filter for event", self.signalName


    def getChangeMethod(self):
        ''' 
        Return widget's method that handles event. 
        
        In Qt, by convention, the handler has the same name as the event, except for capitalization.
        '''
        # Return function object of widget's method having same name as this ProxyEvent
        result = eval( "self.widget." + self.signalName)
        # print "getChangeMethod returns:", result
        return result


    def getGenerationArguments(self, argumentString):
        # print "getGenerationArguments"
        return [QCloseEvent()]  # TODO:
      
      
      