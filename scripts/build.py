"""Inject data/trades.json into site/template.html -> site/index.html"""
import json
t=open('site/template.html').read()
d=json.load(open('data/trades.json'))
open('site/index.html','w').write(t.replace('__DATA__',json.dumps(d,separators=(',',':'))))
print('wrote site/index.html')
