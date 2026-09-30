"""Baixa somente documentação pública para análise local."""
import urllib.request,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];directory=ROOT/'docs/integracoes/fontes';directory.mkdir(parents=True,exist_ok=True)
sources={
 'siconfi-index.html':'https://apidatalake.tesouro.gov.br/docs/siconfi/',
 'pncp-openapi.json':'https://treina.pncp.gov.br/api/pncp/v3/api-docs',
 'pncp-swagger-config.json':'https://treina.pncp.gov.br/api/pncp/v3/api-docs/swagger-config',
}
for name,url in sources.items():
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RioGestao-Documentation/1.0'}),timeout=20) as response:content=response.read(10000000)
  (directory/name).write_bytes(content);print(name,len(content))
  if name.endswith('.html'):print('\n'.join(re.findall(r'<script[^>]*src=[\"\']([^\"\']+)',content.decode('utf-8',errors='replace'))))
 except Exception as error:print(name,type(error).__name__,str(error)[:140])
