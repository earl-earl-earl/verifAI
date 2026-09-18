import asyncio
from urllib.parse import quote, quote_plus

import httpx
from app.models.claim import Source
from bs4 import BeautifulSoup

SOURCES: dict = {
  "REUTERS": "https://www.reuters.com/site-search/?query=",
  "AP_NEWS": "https://apnews.com/search?q=",
  "POLITIFACT": "https://politifact.com/search/?q=",
  # Snopes uses percent
  "SNOPES": "https://www.snopes.com/search/?q="
}

def encode_claim(claim: str) -> tuple[str, str]:
  plus_encoded = quote_plus(claim)
  percent_encoded = quote(claim)
  return (plus_encoded, percent_encoded)

async def fetch_page(url: str) -> str | None:
  try:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"User-Agent": "verifAI-bot/1.0 (+https://github.com/earl-earl-earl/verifAI; fact-checking research)"}, timeout=10.0)
        response.raise_for_status()
        return response.text
  except httpx.HTTPStatusError:
    return None
  except httpx.RequestError:
    return None
    
def extract_content(html: str) -> tuple[str, str]:
  parsed_html = BeautifulSoup(html, "html.parser")
  if parsed_html.title:
    title = parsed_html.title.get_text()
  else:
    title = "No title found"
    
  paragraphs = parsed_html.find_all("p")[:3]
  texts = []
  for p in paragraphs:
    texts.append(p.get_text())
  snippets = " ".join(texts)
  
  return (title, snippets)
  
  
async def scrape_source(url: str) -> Source | None:
  html = await fetch_page(url)
  if html:
    result = extract_content(html)
    title, snippet = result
    return Source(url=url, title=title, snippet=snippet)
  else:
    return None

async def scrape_evidence(claim: str) -> list:
  urls = []
  for source, endpoint in SOURCES.items():
    if source == "SNOPES":
      urls.append(f"{endpoint}{encode_claim(claim)[1]}") # percent-encoded for snopes
    else:
      urls.append(f"{endpoint}{encode_claim(claim)[0]}") # plus-encoded for the rest
  
  tasks = []
  for url in urls:
    tasks.append(scrape_source(url))
  
  filtered_results = []
  results = await asyncio.gather(*tasks, return_exceptions=True)
  for result in results:
    if result is None or isinstance(result, Exception):
      pass
    else:
      filtered_results.append(result)
  return filtered_results