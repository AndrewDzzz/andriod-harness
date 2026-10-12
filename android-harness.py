"""Repository launcher; the same runner is also shipped in the skill."""
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    scripts = Path(__file__).resolve().parent / 'scripts'
    sys.path.insert(0, str(scripts))
    runpy.run_path(str(scripts / 'run.py'), run_name='__main__')
