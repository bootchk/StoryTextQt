

from ..eventFilter import StorytextQtEventFilter
from happeningEventProxy import QtEventProxy


class QtViewportEventProxy(QtEventProxy):
    '''
    Proxy for a (low-level) QEvent that is viewported.
    
    "Appears" to StoryText to be "on" e.g. a QGraphicsView.
    But event filter is installed on *viewport* of QGraphicsView, 
    i.e. an anonymous child (of type QWidget) beside scroll bars.
    In Qt, the scrolled pane of a QGraphicsView is just a QWidget (displaying a QGraphicsScene.)
    '''

    def getRealWidget(self):
        '''
        Widget to receive generated event is viewport.
        
        Reimplemented.
        '''
        return self.widget.widget.viewport()
