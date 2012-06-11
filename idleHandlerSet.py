from PySide.QtCore import QObject, QAbstractEventDispatcher


class HandlerSet(QObject):
  '''
  A set of event loop handlers (timers.)
  
  Why is it a set?
  For now, there is only one idle handler at a time,
  either idleReplayHander or idleDescribeHandler.
  Also, storytext might need a delayHandler.
  IOW, lkk I don't understand the requirements yet.
  !!! Currently, only one handler is ever installed.
  A dictionary is used because access is keyed by handlerID, not because it has more than one row.
  But also, I am not sure that StoryText doesn't install multiple timers concurrently???
  !!! Also there is no method to indicate the app has quit (and event loop stopped.)
  I don't understand why storytext installs a describerHandler after a replayHandler finishes reading a usecase,
  without starting and stopping the event loop?
  Does storytext execute many usecases on the same running SUT?  For shortcuts?
  
  Responsibility:
  - know event loop
  - add and delete handlers (start and stop)
  - dispatch timer expirations (timeouts)
  - perform various adaptations for generic storytext:
  -- delay install idle handlers until event loop is created
  -- stop a handler when another is attempted to start in its place **
  
  ** Generic StoryText assumes a GTK model, where a handler stops if it returns false.
  Here we stop a handler (for example a replayHandler) if another (a describerHandler) is started.
  This is a hack to avoid patching generic storytext.
  If there is a requirement for multiple concurrent handlers, this must be changed.
  
  Stereotype: Coordinator
  
  Specialized for Qt.
  Inherits QObject, which implements timers in Qt.
  
  Class invariant:
  self.eventLoop is not None and self.handlers[] has one row keyed by handlerID   and self.delayedHandler is None
   or self.eventLoop is None and self.handlers[] is empty                         and self.delayedHandler is a idleHandler method
  
  In other words three states:
  1.  No timers installed
  2.  A handler specified to be installed but delayed until the event loop exists.
  3.  A single timer installed.
  '''
  
  def __init__(self):
    super(HandlerSet, self).__init__()
    self.handlers = {}  # map id to method
    self.eventLoop = None
    self.delayedHandler = None

    """
    These are attempts to capture event loop without requiring SUT to be harnessed
    with call to setSUTReady.
    
    This doesn't work yet because Storytext messes the signal?
    # Set alarm signal handler and a 10-second alarm
    signal.signal(signal.SIGALRM, self.captureApplicationAndStartDelayedIdleHandlers)
    signal.alarm(10)
    
    This doesn't work.  Because it is a separate thread from the app?
    # Start a Python timer to later capture the event loop
    timer = Timer(20, self.captureApplicationAndStartDelayedIdleHandlers)
    timer.start()
    """
    
  
  def captureApplicationAndStartDelayedIdleHandlers(self):
    ''' 
    Capture the SUT event loop and install delayed handlers. 
    
    Precondition: event loop exists.
    QAED.instance() classmethod is available before event loop (QApplication) is created.
    Raises exception if called before event loop is created.
    '''
    self.eventLoop = QAbstractEventDispatcher.instance()
    # 0 returned if no event loop
    if self.eventLoop == 0:
      # logger not exist?
      # self.logger.debug("No event loop yet?")
      raise RuntimeError, "Failed to capture event loop."
    else:
      print "Captured event loop"
      if self.delayedHandler is not None:
        self._installDelayedHandler()
  
  
  def _installDelayedHandler(self):
    '''
    Install a handler that was delayed until event loop exists.
    
    Precondition: a handler was delayed.
    '''
    assert self.delayedHandler is not None
    # Install delayed idle handler
    timerID = self._idleAdd(self.delayedHandler)
    self.delayedHandler = None
    
    # Note IdleHandlerUseCaseReplayer.idleHandler is supposed to shadow this ???
    # Here we can't access it.  If we return None ????
      
    
  def idleAdd(self, method, priority):
    ''' 
    Try to add handler to be called each iteration of event loop.
    Return ID or None (if delayed.)
    Note that caller (IdleHandlerUseCaseReplayer) is keeping a reference to the result.
    
    Differs from other GUI TK's: delays adding idle handler until later if not exist event loop.
    
    Implementation in Qt is a timer with time=0 (called every iteration of event loop.)
    Call methods of inherited QObject.
    '''
    # print "idleAdd", method
    if self.eventLoop is None:
      # print "Delay adding idle handler until event loop exists"
      self.delayedHandler = method
      return None
    else:
      return self._idleAdd(method)
   
  
  def _idleAdd(self, method):
    ''' 
    Add idle handler to event loop and return its ID.
    
    Precondition: event loop exists so can create timers on it.
    Postcondition: only one timer is active
    '''
    # Stop any running timers as soon as possible to avoid race
    self.stopAnyTimers()
    
    # call QObject.startTimer()
    timerID = self.startTimer(0) # Zero means every iteration of event loop
    if timerID == 0:
      raise RuntimeError, "Could not start timer, no event loop?"
    else:
      self.handlers[timerID]=method
    return timerID
   

  def stopAnyTimers(self):
    ''' Stop any idleHandlers already running. '''
    for key in self.handlers.keys():
      self._removeHandler(key)
  
  
  # TODO: since we are returning handlerID, a client could call this??
  def _removeHandler(self, handlerID):
    ''' 
    Stop and remove (kill) a handler.
    Note there may be race conditions.
    '''
    # call QObject.killTimer (only superficially different from QTimer.stop())
    self.killTimer(handlerID)
    del self.handlers[handlerID]
    
    
  def timerEvent(self, event):
    ''' 
    Callback for timer expired. Dispatch on ID to real handler method. 
    In Qt, timer is periodic: continues to run.
    
    An interface adapter; we can't connect timeout directly to real handler method because of parameter mismatch.
    '''
    # print "dispatch timerEvent"
    self.handlers[event.timerId()]()  # method call


'''
TODO:
'''
def timeoutAdd(self, time, method, priority):
    ''' Add a timer with non-zero delay. '''
    raise NotImplementedError
  