DEBUG = True
if DEBUG == True:
    def dprint(*args, **kargs):
        print('\033[94mINFO\033[0m', *args, **kargs)

    def sprint(*args, **kargs):
        print('\033[92mSPEC\033[0m', *args, **kargs)

    def wprint(*args, **kargs):
        print('\033[91mWARN\033[0m', *args, **kargs)
else:
    def dprint(*args, **kargs):
        pass
    def sprint(*args, **kargs):
        pass
    def wprint(*args, **kargs):
        pass
