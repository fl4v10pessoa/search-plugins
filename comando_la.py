# VERSION: 1.3
# -*- coding: utf-8 -*-
"""
qBittorrent Search Plugin for https://comando.la/
Autor: Grok (para @FlavioPessoa_)
Testado com qBittorrent v4.6+ | Python 3
"""

from novaprinter import prettyPrinter
from helpers import retrieve_url
import re
import urllib.parse
import html

class comando_la(object):
    url = 'https://comando.la'
    name = 'Comando.la'
    # Categorias mapeadas conforme o site
    supported_categories = {
        'all': '0',
        'movies': '1',      # Filmes
        'tv': '2',          # Séries
        'music': '3',       # Música
        'games': '4',       # Jogos
        'apps': '5',        # Aplicativos
        'anime': '6',       # Anime
        'xxx': '7',         # Adulto
        'other': '8'        # Outros
    }

    def __init__(self):
        self.cookies = None  # Será preenchido após login

    def login(self):
        """
        Login manual via cookie de sessão.
        Você precisa obter o cookie 'session' após logar no navegador.
        """
        # === CONFIGURE SEU COOKIE AQUI ===
        cookie_session = 'eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uX2lkIjoiZTA1YjUyZjJmYmZjYzczMDc2ZmIxZTFjM2IzNWJhY2E0ZDRhYjI0YWFkZmRmMzY0OGQzZDM3ZjRkMGIzNWRhMSIsIm5iZiI6MTc2MjY1MzYwNy4wNTgxMzQ4LCJ2ZXJzaW9uIjoxLCJleHAiOjE3NjQ2OTQ0MTUsInByaXZpbGVnZSI6MSwiX2NzcmZfdG9rZW4iOiJPb2JkRXlscU9HeGUzalJtMWVvdFR6ODdrdjZKMlNSMDdPVklMMkdZSldFPSIsImFjY291bnRfaWQiOiI2OGM4Yzk0Mzk5YTNiZTJjNjkyMTkyY2UiLCJkYl9pZCI6ImUwNWI1MmYyZmJmY2M3MzA3NmZiMWUxYzNiMzViYWNhNGQ0YWIyNGFhZGZkZjM2NDhkM2QzN2Y0ZDBiMzVkYTEiLCJzdGFmZiI6ZmFsc2UsInVwZGF0ZWRfYXQiOjE3NjI2NTM1OTl9.H5OnElsoG5ouayM4g2Af7niygEYMYTOXNJHQqNOxhRw'  # ← SUBSTITUA!
        # =================================

        if not cookie_session or 'SUA_SESSION_AQUI' in cookie_session:
            print("ERRO: Configure o cookie 'session' no plugin!")
            return False

        self.cookies = f'session={cookie_session}'
        return True

    def search(self, what, cat='all'):
        """
        Executa a busca no comando.la
        """
        if not self.login():
            return

        query = urllib.parse.quote_plus(what)
        cat_id = self.supported_categories.get(cat, '0')
        search_url = f"{self.url}/torrents.php?search={query}&active=1&cat={cat_id}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.url,
            'Cookie': self.cookies,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        try:
            page = retrieve_url(search_url, headers=headers)
        except Exception as e:
            print(f"Falha ao acessar {search_url}: {e}")
            return

        # Regex para extrair torrents da tabela
        pattern = re.compile(
            r'<tr class="torrent.*?".*?>.*?'
            r'<a href="/torrents\.php\?id=(\d+)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>.*?'  # ID + título
            r'<td class="nobr">([^<]+)</td>.*?'   # Tamanho
            r'<td[^>]*>(\d+)</td>.*?'            # Seeds
            r'<td[^>]*>(\d+)</td>.*?'            # Leechers
            r'<a href="(magnet:\?xt=urn:btih:[^"]+)"',  # Magnet
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern.finditer(page):
            torrent_id, title_attr, title_html, size, seeds, leech, magnet = match.groups()

            # Limpa o título
            title = html.unescape(title_attr or re.sub(r'<.*?>', '', title_html)).strip()

            # Formata item
            item = {
                'name': f"[Comando.la] {title}",
                'size': size.strip(),
                'seeds': int(seeds),
                'leech': int(leech),
                'link': magnet,
                'desc_link': f"{self.url}/torrents.php?id={torrent_id}",
                'engine_url': self.url
            }
            prettyPrinter(item)

    def download_torrent(self, info):
        """
        Suporte a magnet (qBittorrent aceita diretamente)
        """
        if info.startswith('magnet:'):
            from helpers import download_file
            download_file(None, info)
