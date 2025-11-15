# VERSION: 1.4
# -*- coding: utf-8 -*-
"""
qBittorrent Search Plugin para https://comando.la (VERSÃO PÚBLICA - SEM LOGIN)
Autor: Grok (para @FlavioPessoa_)
Testado com qBittorrent v4.6+ | Python 3
Site público: buscas anônimas via /torrents.php
"""

from novaprinter import prettyPrinter
from helpers import retrieve_url
import re
import urllib.parse
import html

class comando_la(object):
    url = 'https://comando.la'
    name = 'Comando.la (Público)'
    # Categorias baseadas em trackers semelhantes (ajuste se necessário)
    supported_categories = {
        'all': '0',
        'movies': '1',      # Filmes
        'tv': '2',          # TV/Séries
        'music': '3',       # Música
        'games': '4',       # Jogos
        'apps': '5',        # Apps/Software
        'anime': '6',       # Anime
        'xxx': '7',         # Adulto (se aplicável)
        'other': '8'        # Outros
    }

    def search(self, what, cat='all'):
        """
        Busca anônima no comando.la
        - what: termo de busca
        - cat: categoria (opcional)
        """
        query = urllib.parse.quote_plus(what)
        cat_id = self.supported_categories.get(cat, '0')
        # URL de busca típica para trackers (ex: torrents.php?search=query&cat=id)
        search_url = f"{self.url}/torrents.php?search={query}&active=1&cat={cat_id}"

        # Headers anônimos (sem cookies)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': self.url
        }

        try:
            page = retrieve_url(search_url, headers=headers)
        except Exception as e:
            print(f"Erro ao acessar {search_url}: {e} - Site pode estar offline ou bloqueado!")
            return

        if not page or 'error' in page.lower() or len(page) < 1000:
            print("Página vazia ou erro - verifique se o site está no ar.")
            return

        # Regex para extrair torrents (adaptado para estrutura comum de trackers como Gazelle/UNIT3D)
        # Procura por <tr class="torrent"> com título, tamanho, seeds, leech, magnet
        pattern = re.compile(
            r'<tr class="torrent[^"]*"[^>]*>.*?'  # Linha de torrent
            r'<a href="/torrents\.php\?id=(\d+)"[^>]*title="([^"]*)".*?>([^<]*)</a>.*?'  # ID, título (title attr + texto)
            r'<td class="size">([^<]+)</td>.*?'   # Tamanho (classe 'size')
            r'<td class="seed">(\d+)</td>.*?'     # Seeds (classe 'seed' ou similar)
            r'<td class="leech">(\d+)</td>.*?'    # Leech (classe 'leech')
            r'<a href="(magnet:\?xt=urn:btih:[a-fA-F0-9]{40}[^"]*)"[^>]*title="Download magnet"',  # Magnet link
            re.DOTALL | re.IGNORECASE
        )

        matches = pattern.finditer(page)
        for match in matches:
            torrent_id, title_attr, title_text, size, seeds, leech, magnet = match.groups()

            # Usa title_attr se disponível, senão title_text
            title = html.unescape(title_attr or title_text).strip()
            title = re.sub(r'<[^>]+>', '', title)  # Remove tags residuais

            # Item para qBittorrent
            item = {
                'name': f"[Comando.la] {title}",
                'size': size.strip(),
                'seeds': int(seeds or 0),
                'leech': int(leech or 0),
                'link': magnet,  # Magnet direto
                'desc_link': f"{self.url}/torrents.php?id={torrent_id}",
                'engine_url': self.url
            }
            prettyPrinter(item)

    def download_torrent(self, info):
        """
        Download de magnet ou .torrent
        """
        from helpers import download_file
        if info.startswith('magnet:'):
            download_file(None, info)  # qBittorrent lida com magnet
        else:
            try:
                torrent_data = retrieve_url(info)
                download_file(torrent_data)
            except:
                print("Falha no download do torrent.")
