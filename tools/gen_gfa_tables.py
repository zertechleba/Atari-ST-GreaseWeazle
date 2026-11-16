"""Prevede tabulky tokenu z gfalist (tables.c) do src/gfa_tables.js.

    python tools/gen_gfa_tables.py cesta/k/gfalist/tables.c
"""
import json, os, re, sys
src=open(sys.argv[1],encoding='latin1').read()
def table(name):
    body=src[src.index(name):]; body=body[body.index('{')+1:body.index('\n};')]
    body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
    out=[]
    for m in re.finditer(r'NULL|"((?:\\x[0-9A-Fa-f]{2}|[^"\\])*)"',body):
        if m.group(0)=='NULL': out.append(None)
        else: out.append(re.sub(r'\\x([0-9A-Fa-f]{2})',lambda x:chr(int(x.group(1),16)),m.group(1)))
    return out
def js(name,t):
    while t and t[-1] is None: t.pop()
    return 'const %s = %s;'%(name, json.dumps([x if x is not None else 0 for x in t],ensure_ascii=True,separators=(',',':')))
l,p,s=table('gfalct[512]'),table('gfapft[256]'),table('gfasft[256]')
print(len(l),len(p),len(s))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src','gfa_tables.js'),'w').write('\n'.join([js('GFA_LCT',l),js('GFA_PFT',p),js('GFA_SFT',s)])+'\n')
