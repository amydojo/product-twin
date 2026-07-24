from __future__ import annotations
import argparse,json
from pathlib import Path
from .service import render_fixture

def main():
    p=argparse.ArgumentParser(prog='product-twin'); sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('render-fixture'); r.add_argument('--spec',type=Path,required=True); r.add_argument('--output',type=Path,required=True); r.add_argument('--no-fallback',action='store_true')
    a=p.parse_args()
    if a.command=='render-fixture': print(json.dumps(render_fixture(a.spec,a.output,allow_fallback=not a.no_fallback),indent=2))
if __name__=='__main__': main()
