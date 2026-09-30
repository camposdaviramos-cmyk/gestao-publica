"""Verifica a instalação ativa sem autenticar nem alterar dados do usuário."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8080');page.wait_for_selector('#auth-form')
 assert page.evaluate("typeof prepareERP === 'function' && typeof erpPage === 'function'")
 assert page.evaluate("erpBalanceValue('last_timestamp',202601021230)")=='02/01/2026 12:30'
 assert page.evaluate("erpBalanceValue('last_meter',123450000)")=='123,45'
 assert page.evaluate("accessible('entities') === false && accessible('social_confidential') === false")
 assert page.evaluate("typeof esocialList === 'function' && typeof directoryBindings === 'function' && typeof annexFilter === 'function'")
 assert page.request.get('http://127.0.0.1:8080/api/esocial/batches').status==401
 assert page.request.get('http://127.0.0.1:8080/api/signatures/1/download').status==401
 assert not errors,errors
 browser.close();print('Instalação ativa: scripts carregados, login disponível, navegação e formatação conferidas; nenhum erro JavaScript.')
