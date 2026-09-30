"""Gera uma matriz que mantém cada cláusula encontrada no recorte fornecido."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'docs'/'edital-extraido.txt').read_text(encoding='utf-8')
items=[]
specific={
 '4.36':('Parcial','Autenticação, senhas fortes, classificação no cadastro e mínimo parametrizável. A adoção de senhas fracas é deliberadamente bloqueada; validar a política com a contratante.'),
 '4.37':('Implementado','Ajuda contextual acessível no cabeçalho e no menu; tutoriais internos.'),
 '4.38':('Parcial','Interface web responsiva. Acesso pela Internet depende de implantação em servidor HTTPS e infraestrutura institucional.'),
 '4.39':('Implementado','Bloqueio por tentativas, prazo configurável, troca obrigatória, invalidação de sessões e recuperação local auditada.'),
 '4.40':('Implementado','Dias e horários por usuário, com validação em cada requisição no fuso America/Sao_Paulo.'),
 '4.41':('Implementado','Grupos com permissões por módulo; alterações aplicadas aos usuários vinculados.'),
 '4.42':('Implementado','Dupla custódia por módulo para inclusão, alteração e exclusão; proibição de autoaprovação; controle de versão.'),
 '4.43':('Parcial','Permissões por usuário/grupo para consulta, gravação, exclusão e aprovação. Dupla custódia configurada por módulo, não por usuário/operação; cadastros administrativos não têm fluxo de dupla custódia.'),
 '4.44':('Implementado','Auditoria persistente de login autorizado e recusado, com data, hora, usuário e origem.'),
 '4.45':('Parcial','Validação imediata HTML nos campos tipados e senha; validação integral no servidor. O Anexo III foi catalogado; há regras especializadas implementadas e pendências na matriz própria do anexo.'),
 '4.46':('Parcial','Aplicação web servida centralmente, sem instalação por estação; arquivos revalidados ao recarregar. Implantação automatizada e gestão de versões em produção pendentes.'),
 '4.47':('Implementado','Atalhos HTTPS personalizados por usuário, com inclusão e remoção na interface.'),
 '4.48':('Implementado','Rotinas de manutenção homologadas executadas pela interface; scripts protegidos com Fernet em repouso e execução auditada.'),
 '4.49':('Implementado','Prévia em tela, PDF, XLSX, CSV e DOCX; download e impressão pelo navegador, incluindo seleção de páginas, cópias e impressora disponibilizadas pelo sistema operacional.'),
 '4.50':('Parcial','Auditoria de login, dashboard, consultas de registros, alterações, exclusões, relatórios e decisões. Acesso a todas as páginas auxiliares e auditoria exportada imutável externa ainda não implementados.'),
 '4.51':('Parcial','Configuração de exigência de assinatura por relatório ou global. Exportação bloqueada quando exigida; assinatura criptográfica de documentos depende de integração de certificado institucional.'),
 '4.52':('Implementado','Chamados internos com situações, comentários, solução provisória, solução definitiva e notificações internas consultadas a cada 30 segundos.'),
}
def classify(identifier):
 base='.'.join(identifier.split('.')[:2]); n=int(identifier.split('.')[1])
 if base in specific:return specific[base]
 if n<=8:return ('Parcial' if n in [1,6,7] else 'Operacional','Tutoriais EAD com progresso individual implementados. Produção de vídeos, treinamento presencial de 30 usuários em até 40h, limite de 8h/dia, estrutura, custos e aceite dependem da execução contratual.')
 if n==9:return ('Dependência externa','Referências legais preservadas no texto-fonte. Conformidade jurídica e políticas institucionais exigem avaliação dos responsáveis; esta entrega não emite certificação legal.')
 if 10<=n<=18:return ('Parcial' if n in [15,17] else 'Operacional','Chamados registram prioridades, prazos de resposta e solução, comentários e workaround. Horas úteis usam 08h–17h, segunda a sexta, com feriados configuráveis. Equipe, atendimento presencial, acordos e garantias são obrigações operacionais; extensão aceita pela fiscalização não tem fluxo específico.')
 if 19<=n<=22:return ('Parcial','Cadastro de implantação e ordens de serviço disponível. Migração real, continuidade paralela, cronograma contratual e validação dos módulos prioritários dependem das bases legadas, infraestrutura e especificações ausentes.')
 if 23<=n<=32:return ('Parcial','Controle de acesso, cookies HttpOnly/SameSite, proteção CSRF, hash de senha, auditoria e backups/scripts criptografados implementados. TLS, criptografia do disco, cofre de chaves, descarte, devolução de dados e políticas de sigilo devem ser implantados e verificados institucionalmente.')
 if 33<=n<=35:return ('Parcial','Interface em português, responsiva, claro/escuro, navegação por teclado e redução de movimento. Avaliação formal de acessibilidade, privacidade, impactos ambientais e testes com usuários pendentes.')
 if n==53:return ('Dependência externa','Nenhuma nuvem contratada ou provisionada. Redundância geográfica, SSD, SLA, continuidade, capacidade e recuperação precisam ser comprovados por provedor e testes do ambiente produtivo.')
 if 54<=n<=66:return ('Operacional','Obrigação de projeto, implantação, atualização, equipe, atendimento, sustentabilidade ou contratação. Há cadastros para apoio à implantação e OS; atendimento contratual depende da organização responsável e do termo completo.')
 if 67<=n<=81:return ('Dependência externa','Regras de prova de conceito preservadas. Anexo III recebido e catalogado; faltam implementação integral dos módulos, integrações e nuvem homologada. Não é possível calcular percentual de atendimento válido. Demonstração, gravações, atas e julgamento dependem da comissão e da solução completa.')
 return ('Operacional','Garantia contratual e condições de apólice são obrigações documentais/financeiras externas à implementação do sistema.')

segments=re.split(r'\n=== Página (\d+) ===\n',text)
current=None
for index in range(1,len(segments),2):
 page=int(segments[index]); content=segments[index+1]
 content=re.sub(r'EDITAL[^\n]*\n','',content)
 content=re.sub(r'PROCESSO ADMINISTRATIVO[^\n]*\n','',content)
 content=re.sub(r'^\s*'+str(page)+r'\s*$','',content,flags=re.M)
 matches=list(re.finditer(r'^\s*(4\.\d+(?:\.\d+)*)\.\s+',content,re.M))
 if current and matches: current['text']+=' '+content[:matches[0].start()].strip()
 for i,match in enumerate(matches):
  identifier=match.group(1); raw=content[match.end():matches[i+1].start() if i+1<len(matches) else len(content)]
  status,evidence=classify(identifier)
  current={'id':identifier,'page':page,'text':re.sub(r'\s+',' ',raw).strip(),'status':status,'evidence':evidence}; items.append(current)
 if not matches and current: current['text']+=' '+re.sub(r'\s+',' ',content).strip()

result={'source':'Edital PE 552/2026, páginas 35 a 48; processo 44505/2025 – GOVTIC','scope':'Matriz de implementação local. Não comprova atendimento integral ao edital ou aprovação em POC.','items':items}
(ROOT/'docs'/'requisitos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Matriz de rastreabilidade do recorte fornecido','',result['source'],'',result['scope'],'','Cada cláusula foi preservada com texto e referência de página. A numeração 4.1 se repete no documento original.','']
for item in items:lines += [f"## {item['id']} — página {item['page']}",f"**Situação: {item['status']}**",'',item['text'],'',f"**Evidência / dependência:** {item['evidence']}",'']
(ROOT/'docs'/'MATRIZ-REQUISITOS.md').write_text('\n'.join(lines),encoding='utf-8')
print(f'{len(items)} cláusulas preservadas na matriz.')
