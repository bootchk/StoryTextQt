
from PySide.QtCore import QObject

class StorytextQtEventFilter(QObject):
  '''
  Event filter on a widget.
  For certain Qt event types, calls intercept method, then lets event through to widget's event handler(s).
  The net effect is to prefix widget's event handler method for eventType with a call to interceptMethod.
  In other words, "T" the event to the recorder.
  
  This is "installed" on a widget instance, not a particular method of the widget.
  TODO: if requirement for more than one event type per widget....
  
  Not a "filter" in the sense that it stops any events.
  Has internal "filter" to apply interceptMethod to selected events.
  
  TODO discuss QT event filters
  It derives from QObject, there is no "QEventFilter" class.
  discuss event.accept() and ignore() methods
  discuss returning True from event() handler, but not from other, specific handlers()
  '''
  def __init__(self, parent, eventType, interceptMethod, proxyEvent ):
    super(StorytextQtEventFilter, self).__init__(parent)
    self.eventType = eventType
    self.interceptionMethod = interceptMethod
    self.proxyEvent = proxyEvent

  def eventFilter(self, widget, event):
    ''' Method called when GUI TK dispatches event, first to this filter. '''
    # print "Event filter invoked for event type:", event.type()
    # If monitored event type
    if event.type() == self.eventType:
      # print "Intercepted event"
      # Call interception method, passing an instance of HappeningEventProxy
      # Assert interceptionMethod is always recorder.writeEvent() ??
      self.interceptionMethod(self.proxyEvent)
    
    # Always let the event through.  False means: not handled, don't stop the event.
    return False