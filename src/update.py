##try:
##    from manage import internetConnected, checkForHazPyUpdates, checkForToolUpdates
##    checkForHazPyUpdates()
##    checkForToolUpdates()
##
##except:
##    import ctypes
##    import sys
##    messageBox = ctypes.windll.user32.MessageBoxW
##    messageBox(0, "Unexpected error:" + sys.exc_info()[0] + " | If this problem persists, contact hazus-support@riskmapcds.com.", "HazPy",
  
try:
    try:
        from src.manage import internetConnected, checkForHazPyUpdates, checkForToolUpdates
    except:
        from manage import internetConnected, checkForHazPyUpdates, checkForToolUpdates
    checkForToolUpdates()        
    checkForHazPyUpdates()

except:
    import ctypes
    import sys
    messageBox = ctypes.windll.user32.MessageBoxW
    messageBox(0, "Unexpected error:" + str(sys.exc_info()[0]) + " | If this problem persists, contact hazus-support@riskmapcds.com.", "HazPy", 0x1000)
