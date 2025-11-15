# -*- coding: utf-8 -*-
"""
qBittorrent Search Plugin for comando.to
Compatible with qBittorrent 5.1.x and Python 3.9+
"""

import re
import sys
import urllib.parse
from html import unescape
from typing import List, Dict, Any

try:
    from nova_search import SearchPlugin, SearchResult
except ImportError:
    # Fallback para ambiente de desenvolvimento
    class SearchPlugin:
        def search(self, pattern: str, category: str = "") -> List['SearchResult']: ...
    
    class SearchResult:
        def __init__(self, name: str, descr: str, size: int, seeds: int, leech: int, link: str, hash: str = ""): ...

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

http = urllib3.PoolManager(
    cert_reqs='CERT_NONE',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
)

class ComandoSearchPlugin(SearchPlugin):
    name = "Comando.to"
    author = "Plugin by @FlavioPessoa_"
    version = "1.0.2"
    supported_categories = ["all", "movies", "tv", "anime", "apps", "games", "music"]

    base_url = "https://comando.to"
    search_url = f"{base_url}/busca/"

    def search(self, pattern: str, category: str = "all") -> List[SearchResult]:
        if not pattern.strip():
            return []

        query = urllib.parse.quote_plus(pattern.strip())
        url = f"{self.search_url}{query}"

        try:
            response = http.request('GET', url, timeout=10.0)
            if response.status != 200:
                return []

            html = response.data.decode('utf-8', errors='ignore')
            return self.parse_results(html)

        except Exception as e:
            print(f"[Comando.to] Erro na busca: {e}", file=sys.stderr)
            return []

    def parse_results(self, html: str) -> List[SearchResult]:
        results = []
        pattern = re.compile(
            r'<div class="post">.*?'
            r'<a href="(https?://[^"]+)" title="([^"]+)">.*?'
            r'<div class="post-info">.*?'
            r'<span class="size">Tamanho: ([^<]+)</span>.*?'
            r'<span class="seeds">Seeds: (\d+)</span>.*?'
            r'<span class="leechers">Leechers: (\d+)</span>',
            re.DOTALL
        )

        for match in pattern.finditer(html):
            link = match.group(1)
            name = unescape(match.group(2).strip())
            size_str = match.group(3).strip()
            seeds = int(match.group(4))
            leech = int(match.group(5))

            size = self.parse_size(size_str)
            descr = f"Tamanho: {size_str} | Seeds: {seeds} | Leechers: {leech}"

            # Extrai magnet ou .torrent
            torrent_link = self.extract_torrent_link(link)
            if not torrent_link:
                continue

            results.append(SearchResult(
                name=name,
                descr=descr,
                size=size,
                seeds=seeds,
                leech=leech,
                link=torrent_link
            ))

        return results

    def extract_torrent_link(self, detail_url: str) -> str:
        try:
            response = http.request('GET', detail_url, timeout=10.0)
            if response.status != 200:
                return ""

            html = response.data.decode('utf-8', errors='ignore')

            # Procura por link de magnet
            magnet = re.search(r'href="(magnet:\?[^"]+)"', html)
            if magnet:
                return magnet.group(1)

            # Procura por link .torrent
            torrent = re.search(r'href="(https?://[^"]+\.torrent)"', html)
            if torrent:
                return torrent.group(1)

            return ""
        except:
            return ""

    def parse_size(self, size_str: str) -> int:
        size_str = size_str.replace(' ', '').upper()
        multipliers = {
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
            'B': 1
        }
        for unit, multiplier in multipliers.items():
            if unit in size_str:
                try:
                    num = float(size_str.replace(unit, '').replace(',', '.'))
                    return int(num * multiplier)
                except:
                    return 0
        return 0


# Necessário para o qBittorrent
search_plugin = ComandoSearchPlugin()
