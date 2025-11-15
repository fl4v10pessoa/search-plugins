# -*- coding: utf-8 -*-
"""
qBittorrent Search Plugin - comando.to
Autor: @FlavioPessoa_
Versão: 1.1.0
Compatível: qBittorrent 5.1.x | Python 3.9+
"""

import re
import sys
import urllib.parse
from html import unescape
from typing import List

# qBittorrent Nova Search API
try:
    from nova_search import SearchPlugin, SearchResult
except ImportError:
    # Fallback para desenvolvimento
    class SearchPlugin: pass
    class SearchResult:
        def __init__(self, name, descr, size, seeds, leech, link, hash=""):
            self.name = name
            self.descr = descr
            self.size = size
            self.seeds = seeds
            self.leech = leech
            self.link = link
            self.hash = hash

# HTTP Client seguro (ignora SSL se necessário)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

http = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=5.0, read=15.0),
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/130.0.0.0 Safari/537.36'
    },
    cert_reqs='CERT_NONE'
)


class ComandoSearchPlugin(SearchPlugin):
    name = "Comando.to"
    author = "@FlavioPessoa_"
    version = "1.1.0"
    supported_categories = ["all", "movies", "tv", "anime", "games", "apps", "music"]

    base_url = "https://comando.to"
    search_path = "/busca/"

    def search(self, pattern: str, category: str = "all") -> List[SearchResult]:
        if not pattern or not pattern.strip():
            return []

        query = urllib.parse.quote_plus(pattern.strip())
        url = f"{self.base_url}{self.search_path}{query}"

        try:
            resp = http.request('GET', url)
            if resp.status != 200:
                return []

            html = resp.data.decode('utf-8', errors='replace')
            return self._parse_page(html)

        except Exception as e:
            print(f"[comando.to] Erro na requisição: {e}", file=sys.stderr)
            return []

    def _parse_page(self, html: str) -> List[SearchResult]:
        results = []

        # Regex para cada resultado
        item_pattern = re.compile(
            r'<div class="post">\s*'
            r'<a href="(https?://[^"]+)" title="([^"]+)".*?>.*?'
            r'<span class="size">Tamanho: ([^<]+)</span>.*?'
            r'<span class="seeds">Seeds: (\d+)</span>.*?'
            r'<span class="leechers">Leechers: (\d+)</span>',
            re.DOTALL | re.IGNORECASE
        )

        for m in item_pattern.finditer(html):
            detail_url = m.group(1)
            title = unescape(m.group(2)).strip()
            size_str = m.group(3).strip()
            seeds = int(m.group(4))
            leech = int(m.group(5))

            size_bytes = self._parse_size(size_str)
            descr = f"{size_str} • S:{seeds} L:{leech}"

            torrent_link = self._get_torrent_link(detail_url)
            if not torrent_link:
                continue

            results.append(SearchResult(
                name=title,
                descr=descr,
                size=size_bytes,
                seeds=seeds,
                leech=leech,
                link=torrent_link
            ))

        return results

    def _get_torrent_link(self, detail_url: str) -> str:
        try:
            resp = http.request('GET', detail_url, timeout=10.0)
            if resp.status != 200:
                return ""

            html = resp.data.decode('utf-8', errors='replace')

            # 1. Magnet link
            magnet = re.search(r'href="(magnet:\?[^"]+)"', html, re.IGNORECASE)
            if magnet:
                return magnet.group(1)

            # 2. Arquivo .torrent
            torrent = re.search(r'href="(https?://[^"]+\.torrent)"', html, re.IGNORECASE)
            if torrent:
                return torrent.group(1)

            return ""
        except:
            return ""

    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.upper().replace(' ', '').replace(',', '.')
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        for unit, mul in units.items():
            if unit in size_str:
                try:
                    value = float(re.sub(f'[^{unit}0-9.]', '', size_str))
                    return int(value * mul)
                except:
                    return 0
        return 0


# Exporta o plugin
search_plugin = ComandoSearchPlugin()
