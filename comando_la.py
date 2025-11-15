# VERSION: 1.2
# -*- coding: utf-8 -*-
"""
qBittorrent Search Plugin
Name: Comando.la
Author: @FlavioPessoa
Website: https://comando.la
"""

import re
import sys
import urllib.parse
from html.parser import HTMLParser
from typing import List, Dict, Any
import http.client

# Configurações do qBittorrent Search Plugin
PLUGIN_NAME = "Comando.la"
PLUGIN_AUTHOR = "fl4v10pe550a"
PLUGIN_VERSION = "1.2"
PLUGIN_DESCRIPTION = "Busca torrents de filmes e séries no Comando.la"
PLUGIN_URL = "https://comando.la"

# Cabeçalhos para evitar bloqueio
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

class ComandoLaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current = {}
        self.in_article = False
        self.in_title = False
        self.in_link = False
        self.in_size = False
        self.in_quality = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "article" and "post" in attrs.get("class", ""):
            self.in_article = True
            self.current = {"seeds": 0, "peers": 0, "size": "0 MB"}

        elif self.in_article and tag == "a" and "href" in attrs:
            href = attrs["href"]
            if "/comando.la/" in href and not href.endswith("/page/"):
                self.current["link"] = href
                self.in_link = True

        elif self.in_article and tag == "h2" and "entry-title" in attrs.get("class", ""):
            self.in_title = True

        elif self.in_article and tag == "span" and "size" in attrs.get("class", ""):
            self.in_size = True

        elif self.in_article and tag == "img":
            self.current["category"] = attrs.get("alt", "Filme")

    def handle_endtag(self, tag):
        if tag == "article" and self.in_article:
            self.in_article = False
            if "link" in self.current and "name" in self.current:
                self.results.append(self.current)
            self.current = {}
            self.in_title = self.in_link = self.in_size = False

        elif self.in_title and tag == "h2":
            self.in_title = False
        elif self.in_link and tag == "a":
            self.in_link = False
        elif self.in_size and tag == "span":
            self.in_size = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.in_title:
            self.current["name"] = data.replace("Torrent", "").strip()

        elif self.in_size:
            size_match = re.search(r'([\d\.]+)\s*(GB|MB)', data, re.I)
            if size_match:
                size_val = float(size_match.group(1))
                unit = size_match.group(2).upper()
                size_bytes = size_val * (1024**3 if unit == "GB" else 1024**2)
                self.current["size"] = f"{size_val:.2f} {unit}"

        elif self.in_article and "ano" in data.lower():
            year_match = re.search(r'\b(19|20)\d{2}\b', data)
            if year_match:
                self.current["name"] = self.current.get("name", "") + f" ({year_match.group(0)})"


def search(query: str, category: str = "") -> List[Dict[str, Any]]:
    query = urllib.parse.quote_plus(query)
    url = f"https://comando.la/?s={query}"
    results = []

    try:
        conn = http.client.HTTPSConnection("comando.la", timeout=10)
        conn.request("GET", f"/?s={query}", headers=HEADERS)
        response = conn.getresponse()

        if response.status != 200:
            return results

        data = response.read().decode("utf-8", errors="ignore")
        conn.close()

        parser = ComandoLaParser()
        parser.feed(data)

        for item in parser.results[:50]:  # Limita a 50 resultados
            name = item.get("name", "Sem título")
            link = item.get("link")
            size = item.get("size", "0 MB")

            # Extrai magnet da página do item
            magnet = get_magnet_link(link)
            if not magnet:
                continue

            results.append({
                "name": name,
                "size": size,
                "seeds": 999,  # comando.la não mostra seeds
                "peers": 999,
                "link": magnet,
                "desc_link": link,
            })

    except Exception as e:
        print(f"[Comando.la] Erro: {e}", file=sys.stderr)

    return results


def get_magnet_link(page_url: str) -> str:
    try:
        conn = http.client.HTTPSConnection("comando.la", timeout=10)
        path = urllib.parse.urlparse(page_url).path + urllib.parse.urlparse(page_url).query
        conn.request("GET", path, headers=HEADERS)
        response = conn.getresponse()
        if response.status != 200:
            return ""

        data = response.read().decode("utf-8", errors="ignore")
        conn.close()

        # Procura por magnet link
        magnet_match = re.search(r'magnet:\?xt=urn:btih:[a-zA-Z0-9]+', data)
        if magnet_match:
            return magnet_match.group(0)

        # Alternativa: link de torrent
        torrent_match = re.search(r'href=["\']([^"\']*\.torrent)["\']', data)
        if torrent_match:
            torrent_url = torrent_match.group(1)
            if not torrent_url.startswith("http"):
                torrent_url = "https://comando.la" + torrent_url
            return torrent_url

    except:
        pass
    return ""


# === Interface obrigatória do qBittorrent ===
def search_plugins():
    return {
        PLUGIN_NAME: {
            "name": PLUGIN_NAME,
            "author": PLUGIN_AUTHOR,
            "version": PLUGIN_VERSION,
            "desc": PLUGIN_DESCRIPTION,
            "search": search,
        }
    }


if __name__ == "__main__":
    # Teste rápido
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search(query)
        for r in results[:5]:
            print(f"{r['name']} | {r['size']} | {r['link'][:70]}...")
