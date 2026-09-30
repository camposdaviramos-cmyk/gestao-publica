import json, urllib.request
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'docs/integracoes/fontes'
d=json.loads((p/'pncp-openapi.json').read_text(encoding='utf-8'))
for route in ['/v1/usuarios/login','/v1/orgaos/{cnpj}/compras','/v1/orgaos/{cnpj}/contratos']:
 print(route,json.dumps(d['paths'][route],ensure_ascii=False)[:14000])
for name, schema in d['components']['schemas'].items():
 if any(x in name.lower() for x in ['login','compraentrada','contratoentrada']):print(name,json.dumps(schema,ensure_ascii=False))
for name,url in {'siconfi.yaml':'https://apidatalake.tesouro.gov.br/docs/siconfi.yaml','esocial-manual-v1.16.pdf':'https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/996775-manualorientacaodesenvolvedoresocialv1-16.pdf'}.items():
 try:
  with urllib.request.urlopen(url,timeout=25) as r:b=r.read(15000000)
  (p/name).write_bytes(b);print('Downloaded',name,len(b))
 except Exception as e:print(type(e).__name__)
if (p/'esocial-manual-v1.16.pdf').exists():
 from pypdf import PdfReader
 (p/'esocial-manual-v1.16.txt').write_text('\n'.join(x.extract_text() for x in PdfReader(p/'esocial-manual-v1.16.pdf').pages),encoding='utf-8')
