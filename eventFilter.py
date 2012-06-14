
from PySide.QtCore import QObject

class StorytextQtEventFilter(QObject):
  '''
  Event filter on a widget.
  For certain Qt event types, this calls intercept method, then lets event through to widget's event handler(s).
  The net effect is to prefix widget's event handler method for eventType with a call to interceptMethod.
  In other words, "T" the event to the interceptMethod.
  
  This is "installed" on a widget instance, not a particular method of the widget.
  TODO: if requirement for more than one event type per widget....
  
  Not a "filter" in the sense that it stops any events.
  Has internal "filter" to select events on which to apply interceptMethod.
  Not "intercept" in the sense "stop", but in the sense "tap" or "snoop".
  
  TODO discuss QT event filters
  It derives from QObject, there is no "QEventFilter" class.
  discuss event.accept() and ignore() methods
  discuss returning True from event() handler, but not from other, specific handlers()
  '''
  def __init__(self, parent, eventType, interceptMethod, interceptArgs ):
    super(StorytextQtEventFilter, self).__init__(parent)
    self.eventType = eventType
    self.interceptionMethod = interceptMethod
    # list of args to interceptMethod, known at install time
    self.interceptArgs = interceptArgs


  def eventFilter(self, widget, qtEvent):
    ''' Method called when GUI TK dispatches qtEvent, first to this filter. '''
    # print "Event filter invoked for event type:", qtEvent.type()
    # Filter on eventType
    if qtEvent.type() == self.eventType:
      #print "Intercepted event", self.eventType
      '''
      Call interception method with arguments (widget, real QEvent, args known at install time).
      Two cases:
      - interceptionMethod is recorder.writeEvent(args known at install time -> instance of HappeningEventProxy )
      - interceptionMethod is describer.scheduleDescribeCallback(args known at install time -> event type )
      
      !!! recorder.writeEvent searches all the args for an instance of type UserEvent (i.e. HappeningEventProxy)
      and then optionally passes all the args on to outputForScript()
      '''
      self.interceptionMethod(widget, qtEvent, *self.interceptArgs )
    else:
      #print "Not intercept event type:", qtEvent.type(), "in filter type:", self.eventType
      pass
    
    # Always let the event through.  False means: not handled, don't stop the event.
    return False
  
  