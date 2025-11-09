#!/usr/bin/env python3
"""
Fixed SHL Assessment Scraper: Corrected URL, imports, and errors for full catalog scrape.
- Base: https://www.shl.com/solutions/products/product-catalog/?start=0&type=1 (matches train.csv/PDF)
- Imports: Fixed 'selenium' (not 'selenium1')
- Pagination: Fixed scope errors in exceptions
- Defaults: Max 500 assessments, 40 pages for full coverage (~400+ items)
- Excludes: Pre-packaged Job Solutions
- Outputs: JSON with name, url, description (comprehensive), duration, adaptive_support, remote_support, test_type (array)
"""
import argparse
import json
import re
import time
from typing import List, Dict, Optional, Set
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# Fixed import: selenium, not selenium1
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
CATALOG_BASE = "https://www.shl.com/solutions/products/product-catalog/"  # Fixed: /solutions/ path
CATALOG_START = "?start=0&type=1"  # Individual tests filter
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}
def init_selenium_driver():
    """Initialize headless Chrome driver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver
def fetch_page(url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    """Fetch and parse webpage with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f" Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f" Failed after {max_retries} attempts: {e}")
                return None
def get_assessment_links_from_page(soup: BeautifulSoup) -> Set[str]:
    """
    Extract individual assessment links from a single page.
    EXCLUDE pre-packaged job solutions.
    """
    links = set()
    # Look for links in various structures
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Must contain product catalog view path
        if '/product-catalog/view/' not in href:
            continue
        # Build full URL
        if not href.startswith('http'):
            href = f"https://www.shl.com{href}"
        # Clean URL (remove query parameters and fragments)
        href = href.split('?')[0].split('#')[0]
        # Check for exclusion - pre-packaged job solutions
        text = a_tag.get_text().lower()
        parent_text = a_tag.parent.get_text().lower() if a_tag.parent else ''
        exclusion_keywords = [
            'pre-packaged', 'prepackaged', 'job-solution',
            'job solution', 'pre packaged', 'solution package',
            'packaged solution'
        ]
        if any(kw in href.lower() or kw in text or kw in parent_text
               for kw in exclusion_keywords):
            continue
        # Additional check: look for category indicators
        # Individual tests usually have specific patterns
        if 'solution' in href.lower() and 'solution' not in text.lower():
            # URL has 'solution' but link text doesn't - might be a package
            continue
        links.add(href)
    return links
def get_all_assessment_links(base_url: str, max_pages: int = 40) -> List[str]:  # Increased default pages
    """
    Get all assessment links from catalog, handling pagination (up to 40 pages for full ~480 items).
    Uses Selenium to load JS content. Fixed exception scope.
    """
    print("Fetching catalog with Selenium (JS-loaded)...")
    driver = init_selenium_driver()
    wait = WebDriverWait(driver, 20)
    all_links = set()
    items_per_page = 12
    start_values = [i * items_per_page for i in range(max_pages)]
    page_num = 0  # For exception scope
    try:
        for page_num, start in enumerate(start_values, 1):
            page_url = f"{CATALOG_BASE}?start={start}&type=1"
            print(f"\nScraping page {page_num}/{max_pages}: {page_url}")
            driver.get(page_url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/product-catalog/view/']")))
            # Scroll to load lazy content
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            # Extract links using BS4 on rendered HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = get_assessment_links_from_page(soup)
            all_links.update(links)
            print(f" Found {len(links)} new links (total: {len(all_links)})")
            time.sleep(1)  # Polite delay
        print(f"\nTotal unique assessment links found: {len(all_links)}")
        return sorted(list(all_links))
    except TimeoutException:
        print(f"\nTimeout on page {page_num}. Stopping.")
    except Exception as e:
        print(f"\nError on page {page_num}: {e}")
    finally:
        driver.quit()
    return sorted(list(all_links))
def scrape_assessment(url: str) -> Optional[Dict]:
    """
    Scrape individual assessment page.
    Returns dict matching PDF: name, url, description (comprehensive: measures/skills/target/features),
    duration, adaptive_support, remote_support, test_type (array).
    """
    try:
        soup = fetch_page(url)
        if not soup:
            return None
        # Get assessment name from h1 or title
        name = None
        # Try multiple selectors for the name
        name_selectors = ['h1', 'h1.title', '.product-name', '.assessment-name', 'title']
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                # Clean up name
                name = re.sub(r'\s*[-–—|]\s*SHL.*$', '', name, flags=re.I).strip()
                if name and len(name) >= 3:
                    break
        if not name or len(name) < 3:
            # Fallback: extract from URL
            name = url.rstrip('/').split('/')[-1].replace('-', ' ').title()
        # Get page text for analysis
        page_text = soup.get_text(' ', strip=True)
        # Double-check: skip if this is a pre-packaged solution
        exclusion_phrases = [
            'pre-packaged', 'job solution', 'packaged solution',
            'pre packaged', 'solution package'
        ]
        if any(phrase in page_text.lower() for phrase in exclusion_phrases):
            # Check if it's explicitly marked as individual test
            if 'individual test' not in page_text.lower():
                return None
        # ENHANCED DESCRIPTION EXTRACTION (PDF: measures, skills, target, features)
        # Build comprehensive description from multiple sources
        description_parts = []
        # 1. Meta description
        meta = soup.find('meta', {'name': 'description'}) or \
               soup.find('meta', {'property': 'og:description'})
        if meta and meta.get('content'):
            meta_desc = meta['content'].strip()
            if meta_desc and len(meta_desc) > 20:
                description_parts.append(meta_desc)
        # 2. Look for structured content sections (target SHL: "What it measures", etc.)
        content_selectors = [
            ('div[class*="description"], div[class*="what-it-measures"]', 'p'),  # Added SHL-specific
            ('div[class*="overview"]', 'p'),
            ('div[class*="about"]', 'p'),
            ('section[class*="description"]', 'p'),
            ('div[class*="content"]', 'p'),
            ('article', 'p'),
            ('div[id*="description"]', 'p'),
            ('div[id*="overview"]', 'p'),
        ]
        for container_sel, para_sel in content_selectors:
            container = soup.select_one(container_sel)
            if container:
                paragraphs = container.find_all(para_sel)
                for p in paragraphs[:5]:  # Get up to 5 paragraphs
                    text = p.get_text(strip=True)
                    if len(text) > 30 and text not in description_parts:
                        description_parts.append(text)
        # 3. Find all substantial paragraphs if still no description
        if len(description_parts) < 2:
            # Get body content, excluding nav/footer/header
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                for p in main_content.find_all('p'):
                    text = p.get_text(strip=True)
                    # Filter out navigation, short text, and duplicates
                    if (len(text) > 40 and
                        text not in description_parts and
                        not any(nav in text.lower() for nav in ['cookie', 'privacy', 'terms', 'copyright', '©'])):
                        description_parts.append(text)
                        if len(description_parts) >= 5:
                            break
        # 4. Look for bullet points/lists (often contain key features)
        lists = soup.find_all(['ul', 'ol'])
        for ul in lists[:3]:  # Check first 3 lists
            list_items = []
            for li in ul.find_all('li')[:10]:  # Max 10 items per list
                item_text = li.get_text(strip=True)
                if len(item_text) > 10 and len(item_text) < 200:
                    list_items.append(item_text)
            if list_items and len(list_items) >= 2:
                # Add as a formatted section
                list_text = ' | '.join(list_items)
                if list_text not in ' '.join(description_parts):
                    description_parts.append(f"Key features: {list_text}")
        # 5. Combine all parts into comprehensive description
        if description_parts:
            # Join with proper spacing, limit total length
            description = ' '.join(description_parts)
            # Clean up excessive whitespace
            description = re.sub(r'\s+', ' ', description).strip()
            # Limit to reasonable length (first 1000 chars)
            if len(description) > 1000:
                description = description[:997] + '...'
        else:
            # Ultimate fallback: use name and extract keywords from page
            description = name
        # Duration extraction (enhanced)
        duration = None
        duration_patterns = [
            r'(?:duration|time|takes?)[\s:]*(\d+)\s*-\s*(\d+)\s*min',
            r'(?:duration|time|takes?)[\s:]*(\d+)\s*min',
            r'(?:duration|time|takes?)[\s:]*(\d+(?:\.\d+)?)\s*hour',
            r'(\d+)\s*-\s*(\d+)\s*min(?:ute)?s?',
            r'(\d+)\s*min(?:ute)?s?',
            r'(\d+(?:\.\d+)?)\s*hour?s?'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if 'hour' in match.group(0).lower():
                    hours = float(match.group(1))
                    duration = f"{int(hours * 60)} minutes"
                elif len(match.groups()) == 2:
                    duration = f"{match.group(1)}-{match.group(2)} minutes"
                else:
                    duration = f"{match.group(1)} minutes"
                break
        # Test type categorization (enhanced with SHL categories: A,B,C,D,E,K,P,S per PDF)
        test_type = []
        content = f"{name} {description} {page_text[:1000]}".lower()
        # SHL Test Types (from PDF: Ability&Aptitude=A, Biodata&Situational Judgement=B, etc.)
        shl_types = {
            'A': ['ability', 'aptitude'],
            'B': ['biodata', 'situational', 'judgement'],
            'C': ['competencies', 'cognitive', 'numerical', 'verbal', 'reasoning'],
            'D': ['development', '360'],
            'E': ['exercise', 'assessment exercise'],
            'K': ['knowledge', 'skills', 'java', 'python', 'sql', 'programming'],
            'P': ['personality', 'behavior', 'opq', 'trait'],
            'S': ['simulation']
        }
        for code, keywords in shl_types.items():
            if any(re.search(r'\b' + kw + r'\b', content) for kw in keywords):
                test_type.append(code)
        # Fallback if no SHL type found
        if not test_type:
            test_type = ['General']
        # Support flags (per PDF response format)
        adaptive_support = bool(re.search(r'\badaptive\b', page_text, re.IGNORECASE))
        remote_support = bool(re.search(r'\b(?:remote|online|virtual)\b', page_text, re.IGNORECASE))
        return {
            'name': name,
            'url': url,
            'description': description[:500] if description else name,  # Limit description length
            'duration': duration,
            'adaptive_support': adaptive_support,
            'remote_support': remote_support,
            'test_type': test_type
        }
    except Exception as e:
        print(f" Error scraping {url}: {e}")
        return None
def main():
    parser = argparse.ArgumentParser(description="Fixed SHL Assessment Scraper with pagination")
    parser.add_argument('--output', default='assessments_raw.json', help='Output JSON file')
    parser.add_argument('--max', type=int, default=500, help='Maximum assessments to scrape (0 for all)')  # Increased default
    parser.add_argument('--max-pages', type=int, default=40, help='Maximum catalog pages to scrape')  # Increased
    args = parser.parse_args()
    print("="*80)
    print("Fixed SHL Assessment Scraper with Pagination Support")
    print("="*80)
    print(f"\nTarget: {CATALOG_BASE}{CATALOG_START}")
    print(f"Max assessments: {args.max}")
    print(f"Max catalog pages: {args.max_pages}")
    # Get all assessment links (with pagination)
    links = get_all_assessment_links(CATALOG_BASE + CATALOG_START, max_pages=args.max_pages)
    if not links:
        print("\n❌ No assessment links found!")
        print("This could mean:")
        print(" 1. The website structure has changed")
        print(" 2. The website uses JavaScript to load content")
        print(" 3. There are access restrictions")
        return
    print(f"\n{'='*80}")
    print(f"Found {len(links)} total assessment links")
    max_scrape = len(links) if args.max == 0 else min(args.max, len(links))
    print(f"Will scrape up to {max_scrape} assessments")
    print(f"{'='*80}")
    # Scrape each assessment
    assessments = []
    skipped = 0
    print(f"\nScraping individual assessments...")
    for i, url in enumerate(links[:max_scrape], 1):
        print(f"[{i}/{max_scrape}] {url.split('/')[-1][:50]}...", end=' ')
        assessment = scrape_assessment(url)
        if assessment:
            assessments.append(assessment)
            print(f"✓ {assessment['name'][:40]}")
        else:
            skipped += 1
            print("✗ (excluded or error)")
        # Be polite with rate limiting
        if i % 10 == 0:
            print(f" Progress: {i}/{max_scrape}, Collected: {len(assessments)}, Skipped: {skipped}")
            time.sleep(2)
        else:
            time.sleep(0.5)
    # Save results
    print(f"\n{'='*80}")
    print(f"Scraping complete!")
    print(f" ✓ Successfully scraped: {len(assessments)} assessments")
    print(f" ✗ Skipped/Excluded: {skipped}")
    print(f"{'='*80}")
    if not assessments:
        print("\n⚠️ Warning: No valid assessments collected!")
        return
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved to: {args.output}")
    # Statistics
    print(f"\n{'='*80}")
    print("Dataset Statistics:")
    print(f"{'='*80}")
    # Count by test type
    type_counts = {}
    for a in assessments:
        for t in a['test_type']:
            type_counts[t] = type_counts.get(t, 0) + 1
    print("\nTest Type Distribution:")
    for test_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f" {test_type}: {count}")
    # Duration stats
    with_duration = [a for a in assessments if a.get('duration')]
    print(f"\nAssessments with duration info: {len(with_duration)}/{len(assessments)}")
    # Show sample (should now match train.csv, e.g., Java assessments under /solutions/)
    print(f"\n{'='*80}")
    print("Sample assessments:")
    print(f"{'='*80}")
    for i, a in enumerate(assessments[:5], 1):
        print(f"\n{i}. {a['name']}")
        print(f" URL: {a['url']}")
        print(f" Types: {', '.join(a['test_type'])}")
        print(f" Duration: {a['duration'] or 'N/A'}")
        print(f" Description: {a['description'][:100]}...")
    print("\n✅ Done! Run with --max 0 for full scrape.")
if __name__ == '__main__':
    main()