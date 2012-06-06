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
from PySide.QtCore import QEvent

class MouseMoveEvent(QtEventProxy):
    '''
    GUIEvent for the low-level event from Qt to QGraphicsView meaning pointer device (e.g. mouse) has moved.
    '''
    signalName = "mouseMoveEvent"
    eventQtType = QEvent.MouseMove