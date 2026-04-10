import os, sys
base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
os.environ["PATH"] = base + os.pathsep + os.environ.get("PATH", "")
