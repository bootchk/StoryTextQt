


import storytext.guishared
# from PySide.QtGui import QWidget, QLabel

class WidgetAdapter(storytext.guishared.WidgetAdapter):
    ''' 
    Adapt Qt widgets. 
    
    Adaption common to all GUI TK's is in inherited storytext.guishared.WidgetAdapter.
    lkk Not sure what pattern this is, how it works.
    
    !!! Super class __getattr__() allows methods of real widget to be called
    without defining an adaption method in WidgetAdapter.
    So this only defines adaption methods where __getattr__ is not adequate.
    '''
  
    ''' Parent/child relations. '''
  
    def getChildWidgets(self):
        if hasattr(self.widget, "children"):
            return self.widget.children()
        else:
            return []
        
        
    
    ''' Titles, text. '''
          
    def getWidgetTitle(self):
        '''
        Get displayed title of window.
        
        In Qt only makes sense for top level?
        '''
        return self.widget.windowTitle()

    def getLabel(self):
        text = self.getLabelText()
        if text and "\n" in text:
            return text.splitlines()[0] + "..."
        else:
            return text

    def getLabelText(self):
        ''' 
        Get "text" property of widget.
        
        Qt: menu items are QActions which have text() method. 
        '''
        if hasattr(self.widget, "text"):
            return self.widget.text()

    
    
    ''' Programmatic name. '''
    
    def isAutoGenerated(self, name):
      ''' 
      Qt TODO: ??????
      GTK: name.startswith("Gtk")
      '''
      print "Widget name", name
      return True
      

    def getName(self):
        ''' 
        Get programmer supplied name for widget.
        
        Qt: all widgets are QObjects having objectName(). 
        '''
        return self.widget.objectName()
    
    
    ''' Signal and event capabilities. '''
      
    def canWidgetEmitSignal(self, name):
      ''' 
      Does widget emit signal named "name".
      
      !!! Note signal signature looks like a callable method "signal()".
      
      See Qt documentation of QMetaObject.
      A metaobject exists for each Qt class.
      Apparently methods of a metaobject such as indexOfSignal do not consider superclass.
      TODO: ??? need search superclass
      '''
      # Need signal of adapted Qt widget
      widget = self.widget
      widgetMetaObject = widget.metaObject()
      # name must be normalized for Qt metaobject system, and requires str(), and ()
      normalizedName = str(widgetMetaObject.normalizedSignature(name + "()"))
      # print "Normalized name", normalizedName
      widgetHasSignal = widgetMetaObject.indexOfSignal(normalizedName) != -1
      
      # iteratively search super classes for signal
      nextMetaObject = widgetMetaObject.superClass()
      while nextMetaObject is not None and not widgetHasSignal:
        widgetHasSignal = nextMetaObject.indexOfSignal(normalizedName) != -1
        
        """
        print "Dumping methods of metaObject", nextMetaObject.className()
        for i in range(nextMetaObject.methodOffset(), nextMetaObject.methodCount()):
            print str(nextMetaObject.method(i).signature())
        """
           
        nextMetaObject = nextMetaObject.superClass()
      # print "widgetHasSignal returns", widgetHasSignal
      return widgetHasSignal
    
    
    def canWidgetHandleEvent(self, eventName):
      '''
      Does widget have handler for event named "name".
      
      !!! Note many Qt widget classes are documented as having virtual callback methods.
      This discovers whether a SUT author reimplemented (defined) concrete methods?
      
      I believe that that PySide fails to find reimplemented methods in Python (versus C++)
      using metaobjects.
      Hence see below, the use of dir() to find Python methods with desired event name.
      '''
      # Need event of adapted Qt widget
      widget = self.widget
      widgetMetaObject = widget.metaObject()
      # name must be normalized for Qt metaobject system, and requires str(), and ()
      normalizedName = str(widgetMetaObject.normalizedSignature(eventName + "()"))
      print "Normalized name", normalizedName
      '''
      !!! Crux: method of same name as event (but uncapitalized)
      This is Qt convention: handler methods have similar names as QEvents subclasses they handle.
      '''
      widgetHasEvent = widgetMetaObject.indexOfMethod(normalizedName) != -1
      
      # iteratively search super classes
      nextMetaObject = widgetMetaObject.superClass()
      while nextMetaObject is not None and not widgetHasEvent:
        widgetHasEvent = nextMetaObject.indexOfMethod(normalizedName) != -1
        
        """
        print "Dumping methods of metaObject", nextMetaObject.className()
        for i in range(nextMetaObject.methodOffset(), nextMetaObject.methodCount()):
            print str(nextMetaObject.method(i).signature())
        """
            
        nextMetaObject = nextMetaObject.superClass()
        
      # ??? Find reimplemented method in python
      if not widgetHasEvent:
        # un-normalized eventName in dir of real widget
        widgetHasEvent = eventName in dir(widget)
        
      # print "widgetHasEvent returns", widgetHasEvent
      return widgetHasEvent
      
    

storytext.guishared.WidgetAdapter.adapterClass = WidgetAdapter
