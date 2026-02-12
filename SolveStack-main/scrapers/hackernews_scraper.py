"""
Hacker News Scraper

Fetches Ask HN posts from Hacker News using the official Firebase API.
Filters for developer pain points and real-world problems.
Returns normalized problem objects.
"""

import time
import re
from datetime import datetime
from typing import List, Dict
import requests
from text_utils import clean_text as robust_clean_text, truncate_text

# Import centralized logic
from scoring_engine import (
    generate_humanized_explanation,
    classify_solution_type,
    TOPIC_COMPLEXITY
)


# Hacker News API Configuration
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

# Keywords for developer pain points
PAIN_POINT_KEYWORDS = [
    'automation', 'scalability', 'dev tools', 'productivity', 
    'infrastructure', 'deployment', 'ci/cd', 'monitoring', 
    'debugging', 'testing', 'performance', 'optimization',
    'workflow', 'build', 'tooling', 'platform', 'devops'
]


def clean_text(text: str) -> str:
    """Delegated to robust text_utils"""
    return robust_clean_text(text)


def extract_keywords(text: str) -> List[str]:
    """Extract relevant keywords from text"""
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in PAIN_POINT_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Also check for common tech terms from scoring engine
    tech_terms = list(TOPIC_COMPLEXITY.keys())
    
    for term in tech_terms:
        if term in text_lower and term not in found_keywords:
            found_keywords.append(term)
    
    return found_keywords[:5]  # Limit to 5 tags




def is_developer_problem(title: str, text: str) -> bool:
    """Check if the Ask HN post is about a developer pain point"""
    combined = f"{title} {text}".lower()
    
    # Must contain at least one pain point keyword
    has_pain_point = any(kw in combined for kw in PAIN_POINT_KEYWORDS)
    
    # Or common dev-related terms
    dev_terms = ['develop', 'build', 'tool', 'workflow', 'problem', 'solution',
                 'better way', 'automate', 'improve', 'manage']
    has_dev_term = any(term in combined for term in dev_terms)
    
    return has_pain_point or has_dev_term


def scrape_hackernews(limit: int = 10) -> List[Dict]:
    """
    Scrape Ask HN posts from Hacker News.
    
    Args:
        limit: Maximum number of problems to fetch (default: 10)
    
    Returns:
        List of normalized problem dictionaries
    
    Filtering Criteria:
    - Title starts with "Ask HN:" or contains "Ask HN"
    - Story has text (not just a title)
    - Contains developer pain point keywords
    """
    problems = []
    
    try:
        # Get Ask HN story IDs
        print("Fetching Ask HN stories from Hacker News...")
        response = requests.get(f"{HN_API_BASE}/askstories.json", timeout=10)
        
        if response.status_code != 200:
            print(f"HN API returned status code: {response.status_code}")
            return []
        
        story_ids = response.json()
        print(f"Retrieved {len(story_ids)} Ask HN story IDs")
        
        # Fetch individual stories
        checked_count = 0
        for story_id in story_ids:
            if len(problems) >= limit:
                break
            
            # Limit API calls
            if checked_count >= limit * 3:  # Check up to 3x the limit
                break
            
            try:
                # Get story details
                story_response = requests.get(
                    f"{HN_API_BASE}/item/{story_id}.json",
                    timeout=5
                )
                
                if story_response.status_code != 200:
                    continue
                
                story = story_response.json()
                checked_count += 1
                
                if not story:
                    continue
                
                # Extract fields
                title = story.get('title', '').strip()
                text = story.get('text', '').strip()
                
                # Skip if no text
                if not text or len(text) < 50:
                    continue
                
                # Filter for developer problems
                if not is_developer_problem(title, text):
                    continue
                
                # Clean HTML from text
                text_clean = re.sub(r'<[^>]+>', '', text)
                text_clean = clean_text(text_clean)
                
                # Author info
                author = story.get('by', 'Anonymous')
                
                # Date
                timestamp = story.get('time', 0)
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else datetime.now().strftime('%Y-%m-%d')
                
                # Generate fields
                title_clean = re.sub(r'^Ask HN:\s*', '', title, flags=re.IGNORECASE).strip()
                tags = extract_keywords(f"{title} {text_clean}")
                suggested_tech = ', '.join(tags) if tags else 'General Tech'
                humanized_explanation = generate_humanized_explanation(title_clean, text_clean)
                solution_possibility = classify_solution_type(f"{title_clean} {text_clean}", tags)
                
                problem = {
                    'title': robust_clean_text(title_clean),
                    'description': truncate_text(text_clean, 1000),  # Limit description length
                    'source': 'hackernews',
                    'source_id': str(story_id),
                    'reference_link': f"https://news.ycombinator.com/item?id={story_id}",
                    'tags': tags,
                    'suggested_tech': suggested_tech,
                    'humanized_explanation': humanized_explanation,
                    'solution_possibility': solution_possibility,
                    'date': date_str,
                    'author_name': author,
                    'author_id': author
                }
                
                problems.append(problem)
                time.sleep(0.2)  # Be nice to the API
                
            except Exception as e:
                print(f"Error fetching HN story {story_id}: {e}")
                continue
        
        print(f"Scraped {len(problems)} Hacker News problems")
        
    except requests.RequestException as e:
        print(f"Error connecting to Hacker News API: {e}")
    except Exception as e:
        print(f"Error scraping Hacker News: {e}")
    
    return problems


if __name__ == "__main__":
    # Test the scraper
    print("Testing Hacker News scraper...")
    test_problems = scrape_hackernews(limit=5)
    
    if test_problems:
        print(f"\n✓ Successfully scraped {len(test_problems)} problems")
        print("\nSample problem:")
        sample = test_problems[0]
        for key, value in sample.items():
            if key == 'description':
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n✗ No problems scraped")
