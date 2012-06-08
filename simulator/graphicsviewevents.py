""" 
Events for QGraphicsView

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


class MouseMoveEvent(QtEventProxy):
    '''
    GUIEvent for the low-level event from Qt to QGraphicsView meaning pointer device (e.g. mouse) has moved.
    '''
    signalName = "mouseMoveEvent"
    eventQtType = QEvent.MouseMove
    # !!! Many event types (MouseMove, MousePress, etc.) use the same event class
    eventQtFactory = QMouseEvent
    
    
    def getRealEvent(self, argumentString):
        # TODO: reconstruct from argumentString
        point = QPoint(x=10, y=20)
        print "Creating MouseMoveEvent"
        """
        event = self.__class__.eventQtFactory(type=self.__class__.eventQtType,  # enum value e.g. Qt.MouseMove
                                              pos=point,  
                                              button=Qt.LeftButton, # button enum
                                              buttons=Qt.LeftButton, # OR'd bit flag combination (chord) of buttons
                                              modifiers= Qt.NoModifier ) # OR'd bit flag combination (chord) of keyboard modifiers
        """
        event = QMouseEvent(QEvent.MouseMove,
                            point,  
                            Qt.LeftButton, # button enum
                            Qt.LeftButton, # OR'd bit flag combination (chord) of buttons
                            Qt.NoModifier ) # OR'd bit flag combination (chord) of keyboard modifiers
        
        return event