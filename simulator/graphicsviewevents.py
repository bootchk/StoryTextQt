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

#from happeningEventProxy import QtEventProxy
from happeningViewportEventProxy import QtViewportEventProxy
from PySide.QtCore import QEvent, QPoint, Qt
from PySide.QtGui import  QMouseEvent


class MouseEvent(QtViewportEventProxy): # WAS QtEventProxy
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
        ''' Deserialize '''
        args = self._parseArgString(argumentString)
        point = QPoint(args[0], args[1])
        button = self._encodeButton(args[2])
        event = QMouseEvent(self.eventQtType,
                            point,  
                            button, # Qt.NoButton, # button enum
                            button, # Qt.NoButton, # OR'd bit flag combination (chord) of buttons
                            Qt.NoModifier ) # OR'd bit flag combination (chord) of keyboard modifiers
        # print "Created MouseEvent", repr(event), "x is", event.x()
        return event
    
    
    def _parseArgString(self, argumentString):
      ''' List int() conversion of words of argumentString '''
      return map(int, argumentString.split())
      
    def _encodeButton(self, buttonValue):
      if buttonValue == 0:
        return Qt.NoButton
      elif buttonValue == 1:
        return Qt.LeftButton
      elif buttonValue == 2:
        return Qt.RightButton
      elif buttonValue == 4:
        return Qt.MidButton
         
         
    def outputForScript(self, widget, realEvent, *args):
      '''
      Serialize. Return string repr of event and its attributes.
      IOW adapt event to usecase command.
      Called at record time.
      
      Qt has int coords.
      
      Qt NOT have time of event.
      TODO: do we need time and can we construct it?
      
      Note button() returns an enum object, not a numeric object: convert to int then str.
      '''
      return " ".join(( self.name, 
                        str(realEvent.x()),
                        str(realEvent.y()),
                        str(int(realEvent.button())) ))



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