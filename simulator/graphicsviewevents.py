""" 
Events for QGraphicsView.
Low-level events: mouseMove, mouseButtonPress, etc.

Few SUT apps will have QGraphicsView.
When they do, this lets them be tested.

QGraphicsView event dispatching is top down.
Event happening sequence:
=========================
- Qt calls event() method of QGV's QGraphicsScene, passing a QEvent of a particular subclass
- QGraphicsScene event() method:
-- picks (or maintains a *focus*) a QGraphicsItem
-- converts type of event to GraphicsSceneMouseMove (has similar attributes, with coordinates transformed)
-- dispatches QEvent to picked or focused QGraphicsItem mouseMoveEvent()
- events are NOT propagated back up to parents of QGraphicsItems
"""

from happeningEventProxy import QtEventProxy
from PySide.QtCore import QEvent, QPoint, Qt
from PySide.QtGui import  QMouseEvent


class MouseEvent(QtEventProxy):
    '''
    Abstract Base Class for low-level event from Qt meaning input from pointer device (e.g. mouse).
    
    Subclasses: for input in (move, button press, button release.)
    '''
    # provided in subclass
    signalName = None 
    eventQtType = None
    
    # !!! Many Qt event types (MouseMove, MousePress, etc.) use the same event class
    eventQtFactory = QMouseEvent
    
    
    def getRealEvent(self, argumentString):
        # TODO: reconstruct from argumentString
        point = QPoint(x=10, y=20)
        print "Creating MouseEvent"
        event = QMouseEvent(self.eventQtType,
                            point,  
                            Qt.NoButton, # button enum
                            Qt.NoButton, # OR'd bit flag combination (chord) of buttons
                            Qt.NoModifier ) # OR'd bit flag combination (chord) of keyboard modifiers
        return event
      
      
    def outputForScript(self, widget, realEvent, *args):
      '''
      Serialize. Return string repr of event and its attributes.
      IOW adapt event to usecase command.
      Called at record time.
      '''
      # print "ofs called, widget is", happeningProxy, realEvent
      # print "Event ", event.x, " ", event.y
      # Qt has int coords, but not time of event.
      # TODO: do we need time and can we construct it?
      return " ".join(( self.name, str(realEvent.x()), str(realEvent.y()), str(realEvent.button()) ))
      # TODO need decode button



'''
MouseEvent subclasses
'''

class MouseMoveEvent(MouseEvent):
    '''
    Specialization of MouseEvent for pointer *moved*.
    '''
    signalName = "mouseMoveEvent"
    eventQtType = QEvent.MouseMove
    
    
class MouseButtonPressEvent(MouseEvent):
    '''
    Specialization of MouseEvent for pointer *button pressed*.
    '''
    signalName = "mousePressEvent"
    eventQtType = QEvent.MouseButtonPress
    
    
'''
MouseButtonDblClick  4  Mouse press again (QMouseEvent).
QEvent::MouseButtonRelease
'''

# TODO: QEvent::Wheel  31  Mouse wheel rolled (QWheelEvent).