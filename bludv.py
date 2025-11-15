#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Nome do plugin
name = 'BLUDV'
# Descrição
description = 'Plugin de busca para BLUDV Torrents (Filmes e Séries Dublados)'
# Versão
version = '1.1'

# Importações necessárias (qBittorrent fornece helpers.py com essas)
from helpers import retrieve_url
from novaprinter import print_entry  # Para formatar resultados
import re  # Para parsing simples

class SearchPlugin:
    # URL base do mirror (ajuste se necessário)
    page_url = 'https://bludv.to/?s={0}'
    
    def __init__(self):
        pass
    
    # Função principal de busca
    def search(self, what, cat=''):  # 'what' é o termo de busca, 'cat' é categoria (ignorado por simplicidade)
        # Monta a URL de busca
        url = self.page_url.format(what.replace(' ', '+'))  # Substitui espaços por +
        
        # Baixa a página
        try:
            html = retrieve_url(url)
        except Exception as e:
            print(f"Erro ao buscar: {e}", file=open('stderr', 'w'))  # Erros no stderr, não stdout
            return
        
        # Parsing simples do HTML (ajuste seletores baseados no site real)
        # Exemplo: Assume resultados em <div class="torrent-item"> com sub-tags
        pattern = r'<a href="(magnet:[^"]+)".*?>([^<]+)</a>.*?(\d+(?:\.\d+)? [GM]B).*?seeds: (\d+).*?leechers: (\d+)'  # Regex exemplo
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Para cada resultado, formata e imprime
        for link, title, size, seeds, leechers in matches:
            entry = {
                'name': title.strip(),
                'size': size.strip(),
                'link': link,  # Link magnet ou torrent
                'seeds': int(seeds),
                'leechers': int(leechers),
                'engine_url': url  # URL da página de resultados
            }
            print_entry(entry)  # Imprime no formato qBittorrent: link|name|size|seeds|leechers|engine|page_url

# Rode o plugin se chamado diretamente (para testes)
if __name__ == '__main__':
    # Teste: python bludv.py "oppenheimer"
    import sys
    plugin = SearchPlugin()
    plugin.search(sys.argv[1] if len(sys.argv) > 1 else 'test')
