import os
from ZODB.DemoStorage import DemoStorage
from ZODB.FileStorage import FileStorage

dir, name = os.path.split(__file__)
file = os.path.join(dir, 'Data.fs')
fs = FileStorage(file)
Storage = DemoStorage(base=fs, quota=(1<<20))