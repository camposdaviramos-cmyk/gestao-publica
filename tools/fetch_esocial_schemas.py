"""Baixa XSD publicados pelo eSocial e extrai apenas documentos de esquema."""
import hashlib,json,urllib.request,zipfile,io
from pathlib import Path
from lxml import html
ROOT=Path(__file__).resolve().parents[1];target=ROOT/'schemas/esocial';target.mkdir(parents=True,exist_ok=True)
url='https://www.gov.br/esocial/pt-br/documentacao-tecnica'
with urllib.request.urlopen(url,timeout=25) as response:page=html.fromstring(response.read())
chosen={}
for a in page.xpath('//a[@href]'):
 label=a.text_content().strip();href=a.get('href')
 if 'CNPJ alfanumérico' in label and '01/07/2026' in label:chosen['eventos-s1.3-nt06-alfa']=href
 if 'Pacote de Comunicação eSocial v.1.6 - Alfa' in label:chosen['comunicacao-1.6-alfa']=href
 if label=='Pacote de Comunicação eSocial v.1.6':chosen['comunicacao-1.6']=href
if len(chosen)<2:raise RuntimeError('Pacotes oficiais não encontrados.')
manifest=[]
for name,href in chosen.items():
 print('Obtendo',name,href,flush=True)
 with urllib.request.urlopen(href,timeout=30) as response:content=response.read(20000000)
 with zipfile.ZipFile(io.BytesIO(content)) as archive:
  destination=target/name;destination.mkdir(exist_ok=True);count=0
  for entry in archive.infolist():
   if entry.is_dir() or not entry.filename.lower().endswith(('.xsd','.wsdl','.xml')):continue
   path=(destination/entry.filename).resolve()
   if not path.is_relative_to(destination.resolve()) or entry.file_size>10000000:raise RuntimeError('Caminho ou tamanho inválido no pacote.')
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(entry));count+=1
 manifest.append({'package':name,'url':href,'sha256':hashlib.sha256(content).hexdigest(),'files':count})
(target/'manifest.json').write_text(json.dumps({'source':url,'retrieved':'2026-09-23','packages':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=True))
