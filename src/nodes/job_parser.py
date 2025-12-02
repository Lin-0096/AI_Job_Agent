"""Job parser node for extracting job listings from HTML"""

import re
from typing import List
from bs4 import BeautifulSoup


class JobParser:
    """Parse LinkedIn job alert emails to extract job listings"""

    def parse_html(self, html: str) -> List[dict]:
        """Parse HTML and extract job listings (supports both div and table formats)"""
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        seen_links = set()  # Track seen job links to avoid duplicates

        # Try new table-based format first (current LinkedIn format)
        table_jobs = self._parse_table_format(soup)
        for job in table_jobs:
            if job["link"] not in seen_links:
                jobs.append(job)
                seen_links.add(job["link"])

        # Fallback to old div-based format if no table jobs found
        if not jobs:
            job_cards = soup.find_all(attrs={"data-test-id": "job-card"})
            for card in job_cards:
                job = self._extract_job_from_card(card)
                if job and job["link"] not in seen_links:
                    jobs.append(job)
                    seen_links.add(job["link"])

        return jobs

    def _parse_table_format(self, soup) -> List[dict]:
        """Parse jobs from table-based email format (new LinkedIn format)"""
        jobs = []
        
        # Extract HTML as string to search for job-card patterns
        html_str = str(soup)
        
        # Find all job links in the HTML
        job_pattern = r'href="(https://www\.linkedin\.com/comm/jobs/view/\d+[^"]*)"[^>]*>([^<]+)</a>'
        matches = re.findall(job_pattern, html_str)
        
        seen_links = set()
        
        for url, title in matches:
            clean_url = self._clean_linkedin_url(url)
            title = title.strip()
            
            # Skip if already seen or empty title
            if not title or clean_url in seen_links:
                continue
            
            seen_links.add(clean_url)
            
            # Extract company and location from HTML context around the job
            company, location = self._extract_company_location_from_html(html_str, title, clean_url)
            
            job = {
                "title": title,
                "company": company,
                "location": location,
                "link": clean_url,
                "desc": "",
            }
            
            jobs.append(job)
        
        return jobs

    def _extract_company_location_from_html(self, html_str: str, title: str, job_url: str) -> tuple[str, str]:
        """Extract company and location from HTML by finding text near the job title"""
        company = ""
        location = ""
        
        # Escape special regex characters in title
        escaped_title = re.escape(title)
        
        # Look for pattern: "Title" followed by company and location
        # Typically: Title\n\nCompany · Location
        pattern = escaped_title + r'[^·]*·[^<]{0,150}'
        matches = re.findall(pattern, html_str)
        
        if matches:
            match_text = matches[0]
            # Extract the part with " · "
            parts = match_text.split("·")
            if len(parts) >= 2:
                # Get company (text right after title, before ·)
                company_part = parts[0].replace(title, "").strip()
                # Remove HTML entities and extra stuff
                company_part = re.sub(r'[\d;";>\s]+', ' ', company_part)
                company = company_part.strip()
                # Take only the last word(s) that look like a company
                words = company.split()
                if words:
                    company = words[-1]
                
                # Get location (text after ·)
                location = parts[1].strip()
                # Clean up location - remove HTML and extra info
                location = re.sub(r'<[^>]+>', '', location)
                location = location.split('<')[0].strip()
                # Remove common suffixes
                for suffix in ['Easy Apply', 'Save', 'See all jobs', 'Install']:
                    if suffix in location:
                        location = location.split(suffix)[0].strip()
                # Clean extra spaces and newlines
                location = ' '.join(location.split())
        
        return company, location

    def _extract_job_from_card(self, card) -> dict | None:
        """Extract job information from a job card (old div-based format)"""
        try:
            # Find job title link - look for link with text-color-brand class
            title_link = card.find("a", class_=re.compile(r"text-color-brand"))
            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            link = title_link.get("href")

            # Clean up LinkedIn tracking URL
            if link:
                link = self._clean_linkedin_url(link)

            # Find company and location
            company_elem = card.find("p", class_=re.compile(r"text-system-gray"))
            company_text = company_elem.get_text(strip=True) if company_elem else ""

            # Parse company and location from text like "Firemind · Finland (Hybrid)"
            company, location = self._parse_company_location(company_text)

            return {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "desc": "",  # Will be filled later if needed
            }

        except Exception:
            return None

    def _clean_linkedin_url(self, url: str) -> str:
        """Clean LinkedIn tracking parameters from URL"""
        if not url:
            return ""

        # Extract just the base job view URL
        match = re.search(r"(https://www\.linkedin\.com/comm/jobs/view/\d+)", url)
        if match:
            return match.group(1)

        # If URL doesn't have full path, try to construct it
        if url.startswith("/comm/jobs/view/"):
            return f"https://www.linkedin.com{url.split('?')[0]}"

        return url.split("?")[0] if "?" in url else url

    def _parse_company_location(self, text: str) -> tuple[str, str]:
        """Parse 'Company · Location' format"""
        if " · " in text:
            parts = text.split(" · ", 1)
            return parts[0].strip(), parts[1].strip()
        return text.strip(), ""


def parse_jobs(state: dict) -> dict:
    """LangGraph node: Parse jobs from raw HTML emails"""
    parser = JobParser()
    all_jobs = []

    for html in state.get("raw_emails", []):
        jobs = parser.parse_html(html)
        all_jobs.extend(jobs)

    state["jobs"] = all_jobs
    return state
