#!/usr/bin/env python3
"""
Weekly CAC intelligence updater.

Creates a markdown report with:
- Practical reminders for living with CAC > 600
- Fresh PubMed papers from the prior 7 days
- A standing watchlist of plaque-modifying research programs
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List


PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


TOPICS: Dict[str, str] = {
    "High CAC and outcomes": '(("coronary artery calcium"[Title/Abstract] OR "CAC score"[Title/Abstract]) AND (high OR severe OR ">400" OR ">600"))',
    "Plaque regression/remodeling": '("coronary plaque"[Title/Abstract] OR "atheroma"[Title/Abstract]) AND (regression OR remodeling OR progression)',
    "Intensive lipid lowering (statin/PCSK9/ezetimibe/inclisiran)": '((PCSK9 OR inclisiran OR ezetimibe OR statin) AND (coronary OR atherosclerosis OR plaque))',
    "Inflammation and event reduction": '((colchicine OR inflammation) AND (chronic coronary disease OR atherosclerosis))',
    "Lipoprotein(a) and RNA therapeutics": '(("lipoprotein(a)" OR "Lp(a)" OR pelacarsen OR olpasiran) AND (trial OR outcomes OR atherosclerosis))',
}


WATCHLIST = [
    {
        "program": "Lp(a)HORIZON (pelacarsen)",
        "area": "Lipoprotein(a) lowering",
        "why_it_matters": "Tests whether major Lp(a) reduction lowers hard CV outcomes.",
    },
    {
        "program": "OCEAN(a)-Outcomes (olpasiran)",
        "area": "Lipoprotein(a) lowering (siRNA)",
        "why_it_matters": "Large outcomes trial for RNA-based Lp(a) lowering.",
    },
    {
        "program": "PCSK9-pathway intensification programs",
        "area": "Extreme LDL-C reduction",
        "why_it_matters": "Imaging evidence supports plaque burden/composition improvement with very low LDL-C.",
    },
    {
        "program": "Colchicine and inflammation-targeted secondary prevention",
        "area": "Residual inflammatory risk",
        "why_it_matters": "Some trials show event reduction in chronic coronary populations; selection and tolerability remain key.",
    },
]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CalciumScoreAgent/1.0 (educational-use)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CalciumScoreAgent/1.0 (educational-use)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def clean_xml_text(value: str) -> str:
    stripped = re.sub(r"<[^>]+>", "", value)
    return html.unescape(stripped).strip()


def pubmed_search_ids(query: str, days_back: int = 7, max_results: int = 8) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "pub date",
        "datetype": "pdat",
        "reldate": str(days_back),
    }
    url = f"{PUBMED_BASE}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    data = fetch_json(url)
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_fetch_details(pmids: List[str]) -> List[dict]:
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    url = f"{PUBMED_BASE}/efetch.fcgi?{urllib.parse.urlencode(params)}"
    xml = fetch_text(url)

    # Lightweight parsing suitable for stable PubMed XML structure.
    articles = re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml, flags=re.S)
    parsed: List[dict] = []
    for article in articles:
        pmid_match = re.search(r"<PMID[^>]*>(.*?)</PMID>", article, flags=re.S)
        title_match = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", article, flags=re.S)
        journal_match = re.search(r"<Title>(.*?)</Title>", article, flags=re.S)
        year_match = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>.*?</PubDate>", article, flags=re.S)
        doi_match = re.search(
            r'<ArticleId IdType="doi">(.*?)</ArticleId>',
            article,
            flags=re.S,
        )

        pmid = clean_xml_text(pmid_match.group(1)) if pmid_match else ""
        title = clean_xml_text(title_match.group(1)) if title_match else "Untitled"
        journal = clean_xml_text(journal_match.group(1)) if journal_match else "Unknown journal"
        year = year_match.group(1) if year_match else "n.d."
        doi = clean_xml_text(doi_match.group(1)) if doi_match else ""

        parsed.append(
            {
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "year": year,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            }
        )
    return parsed


def build_report(today: dt.date) -> str:
    lines: List[str] = []
    lines.append(f"# Weekly CAC > 600 Research Update ({today.isoformat()})")
    lines.append("")
    lines.append(
        "This report is educational and supports clinician-guided prevention decisions. "
        "It does not replace medical care."
    )
    lines.append("")
    lines.append("## Fast practical checklist")
    lines.append("")
    lines.append("### Continue avoiding")
    lines.append("- Smoking/vaping nicotine")
    lines.append("- Heavy alcohol use")
    lines.append("- Ultra-processed pattern (processed meats, trans fats, sugary drinks, excess sodium)")
    lines.append("- Long sedentary periods")
    lines.append("- Stopping cardiometabolic medications without clinician input")
    lines.append("")
    lines.append("### Continue prioritizing")
    lines.append("- Mediterranean-style eating pattern")
    lines.append("- High-fiber, minimally processed foods")
    lines.append("- Aerobic activity + resistance training as tolerated")
    lines.append("- LDL-C, blood pressure, glucose, sleep, and medication adherence")
    lines.append("- Prompt evaluation of new chest pain, dyspnea, or exertional decline")
    lines.append("")
    lines.append("## New PubMed papers from the last 7 days")
    lines.append("")

    any_papers = False
    for topic, query in TOPICS.items():
        pmids = pubmed_search_ids(query=query, days_back=7, max_results=6)
        papers = pubmed_fetch_details(pmids)
        lines.append(f"### {topic}")
        if not papers:
            lines.append("- No new PubMed items found in the last 7 days for this query.")
            lines.append("")
            continue
        any_papers = True
        for paper in papers:
            title = paper["title"]
            journal = paper["journal"]
            year = paper["year"]
            pmid = paper["pmid"]
            url = paper["url"]
            doi = f"; DOI: {paper['doi']}" if paper["doi"] else ""
            lines.append(f"- **{title}** ({journal}, {year})  ")
            lines.append(f"  PMID: {pmid}{doi}  ")
            lines.append(f"  Link: {url}")
        lines.append("")

    if not any_papers:
        lines.append(
            "_No new papers were returned this week. Consider widening search windows or adding additional queries._"
        )
        lines.append("")

    lines.append("## Emerging plaque-relief/removal research watchlist")
    lines.append("")
    lines.append(
        "No routine clinical therapy currently \"scrapes out\" coronary plaque; current care focuses on "
        "stabilization, event reduction, and in some settings modest regression."
    )
    lines.append("")
    for item in WATCHLIST:
        lines.append(f"- **{item['program']}** ({item['area']}): {item['why_it_matters']}")
    lines.append("")
    lines.append("## Notes for discussion with a clinician")
    lines.append("")
    lines.append("- Are LDL-C targets/intensity adequate for very high risk status?")
    lines.append("- Is additional lipid therapy (ezetimibe/PCSK9-pathway/inclisiran) appropriate?")
    lines.append("- Is elevated Lp(a) present and actionable in trial-era management?")
    lines.append("- Is inflammation-focused prevention (e.g., colchicine in selected patients) appropriate?")
    lines.append("- Are blood pressure, glycemia, sleep apnea, and exercise prescriptions optimized?")
    lines.append("")
    lines.append("---")
    lines.append(f"Generated on {today.isoformat()} by `scripts/weekly_cac_agent.py`")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly CAC>600 update report.")
    parser.add_argument(
        "--output",
        default="reports/weekly/latest-weekly-report.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--update-latest",
        action="store_true",
        help="Also write reports/latest.md.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    today = dt.date.today()
    report = build_report(today=today)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")

    # Also write date-stamped weekly report for history if user kept default output.
    if output_path.name == "latest-weekly-report.md":
        dated_path = output_path.parent / f"{today.isoformat()}.md"
        dated_path.write_text(report, encoding="utf-8")
        print(f"Wrote {dated_path}")

    if args.update_latest:
        latest_path = Path("reports/latest.md")
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        latest_path.write_text(report, encoding="utf-8")
        print(f"Wrote {latest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
