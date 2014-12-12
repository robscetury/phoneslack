from distutils.core import setup
try:
    import py2exe

    setup( windows=["watcher.py"], 
           requires=["Skype4Py"])
except:
    print "Unable to setup windows client.  Make sure you have py2exe installed, and are calling like this:"
    print "python.exe setup.py py2exe"
