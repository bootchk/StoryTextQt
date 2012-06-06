#! /usr/bin/python

'''
Small Qt app for testing storytext Qt adapter
'''

from PySide.QtCore import *
from PySide.QtGui import *
import sys


    
        
class DiagramScene(QGraphicsScene):
    def __init__(self, *args):
        QGraphicsScene.__init__(self, *args)
        self.addItem(QGraphicsTextItem("Small app to test storytext"))
        
        
class GraphicsView(QGraphicsView):
  def __init__(self, parent=None):
      super(GraphicsView, self).__init__(parent)
      
      assert self.dragMode() is QGraphicsView.NoDrag
      
      self.setRenderHint(QPainter.Antialiasing)
      self.setRenderHint(QPainter.TextAntialiasing)

      self.setMouseTracking(True);  # Enable mouseMoveEvent


  ''' Delegate events to FreehandTool. '''
  def mouseMoveEvent(self, event):
    print "GV mouse moved"
    
  def mousePressEvent(self, event):
    print "GV mouse pressed"
    
  def mouseReleaseEvent(self, event):
    print "GV mouse released"
    
    

class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.scene = DiagramScene()
        self.view = GraphicsView(self.scene)
        rect =QRect(-500, -500, 500, 500)
        self.view.fitInView(rect)
        self.view.setSceneRect(rect)
        self.setCentralWidget(self.view)
        
        # hack for storytext
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # So storytext will finish?
        self.setAttribute(Qt.WA_QuitOnClose, True)  # So storytext will finish?
        button = QPushButton("Foo")
        self.setMenuWidget(button)
        button.clicked.connect(self.buttonClicked)

    def buttonClicked(self):
      print "App says button Clicked"
      
    def closeEvent(self, event):
      print "App says main window closed"
      pass
        
        
def main(args):
    app = QApplication(args)
    mainWindow = MainWindow()
    mainWindow.setGeometry(100, 100, 500, 500)
    mainWindow.show()
    
    from storytext import setSUTReady
    setSUTReady()

    sys.exit(app.exec_()) # Qt Main loop


if __name__ == "__main__":
    main(sys.argv)
