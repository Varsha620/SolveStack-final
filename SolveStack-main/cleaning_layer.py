import hashlib
import re
import html
import unicodedata
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple

class DataCleaner:
    """
    Centralized data cleaning and normalization layer for SolveStack.
    Ensures deterministic output and extracts features for deduplication and scoring.
    """
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        # Canonical mapping for tech tags
        self.canonical_tags = {
            "reactjs": "react",
            "react.js": "react",
            "nodejs": "node",
            "node.js": "node",
            "javascript": "js",
            "typescript": "ts",
            "c++": "cpp",
            "c#": "csharp",
            "py": "python",
            "ipynb": "jupyter-notebook",
            "golang": "go",
            "postgresql": "postgres",
            "mongodb": "mongo",
            "kubernetes": "k8s",
            "docker-compose": "docker",
        }

    def clean_problem(self, raw_problem: dict) -> dict:
        """
        Processes a raw problem dictionary into a cleaned and feature-enriched record.
        
        Expected fields in raw_problem:
            raw_title, raw_description, raw_tags, source, date, 
            author_name, author_id, reference_link, source_id
        """
        # 1. Start with metadata and raw fields
        problem = {
            "source": raw_problem.get("source"),
            "source_id": raw_problem.get("source_id"),
            "author_name": raw_problem.get("author_name"),
            "author_id": raw_problem.get("author_id"),
            "reference_link": raw_problem.get("reference_link"),
            "date": self._parse_date(raw_problem.get("date")),
            "scraped_at": raw_problem.get("scraped_at", datetime.utcnow()),
            "cleaned_at": datetime.utcnow(),
            "clean_version": self.version,
            
            # Preserving RAW fields
            "raw_title": raw_problem.get("raw_title"),
            "raw_description": raw_problem.get("raw_description"),
            "raw_tags": raw_problem.get("raw_tags", []),
        }

        # 2. Basic Cleaning
        problem["cleaned_title"] = self._basic_clean(problem["raw_title"])
        problem["cleaned_description"] = self._basic_clean(problem["raw_description"])
        
        # 3. Normalization
        # We store normalized tags in the 'tags' column
        problem["tags"] = self._normalize_tags(problem["raw_tags"])
        problem["normalized_title"] = self._normalize_title(problem["cleaned_title"])
        
        # For backward compatibility / API use
        problem["title"] = problem["cleaned_title"]
        problem["description"] = problem["cleaned_description"]
        problem["suggested_tech"] = ", ".join(problem["tags"])

        # 4. Feature Extraction & Hashing
        problem["title_hash"] = self._generate_hash(problem["normalized_title"])
        
        # Metrics
        problem["text_length"] = len(problem["cleaned_title"]) + len(problem["cleaned_description"])
        problem["word_count"] = len(problem["cleaned_description"].split())
        
        has_code, code_count = self._detect_code(problem["raw_description"])
        problem["has_code_block"] = has_code
        problem["num_code_blocks"] = code_count
        
        # Passthrough scoring fields if present
        for field in ["upvotes", "downvotes", "comment_count", "engagement_score", "difficulty_score"]:
            problem[field] = raw_problem.get(field, 0 if "score" not in field else 0.0)

        # 5. Determine Difficulty Level algorithmically
        problem["difficulty_level"] = self._calculate_difficulty_level(problem["cleaned_title"], problem["cleaned_description"], problem["tags"])

        return problem

    def _calculate_difficulty_level(self, title: str, description: str, tags: List[str]) -> int:
        """
        Determines the difficulty level (1=Beginner, 2=Intermediate, 3=Advanced) based on keyword heuristics.
        """
        content = f"{title} {description}".lower()
        
        advanced_keywords = [
            "distributed", "concurrency", "scaling", "optimization", "orchestration", 
            "kubernetes", "k8s", "microservices", "architecture", "performance", "throughput", 
            "latency", "bottleneck", "memory leak", "race condition", "deadlock", "kernel", "compiler"
        ]
        
        beginner_keywords = [
            "how to", "beginner", "getting started", "tutorial", "simple", "basic", "install", 
            "setup", "error", "typo", "css", "html", "syntax", "what is"
        ]
        
        advanced_hits = sum(1 for kw in advanced_keywords if kw in content)
        beginner_hits = sum(1 for kw in beginner_keywords if kw in content)
        
        # Tag based boosts
        advanced_tags = ["c++", "cpp", "rust", "go", "golang", "kubernetes", "k8s", "docker", "aws", "gcp"]
        if any(tag in advanced_tags for tag in tags):
            advanced_hits += 2
            
        if advanced_hits >= 1:
            return 3 # Advanced
        elif beginner_hits >= 1 and advanced_hits == 0:
            return 1 # Beginner
        else:
            return 2 # Intermediate

    def _basic_clean(self, text: str) -> str:
        """Removes HTML noise and normalizes whitespace while preserving content."""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace but keep single spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _normalize_title(self, title: str) -> str:
        """Lowers case, trims, and removes common noise prefixes."""
        if not title:
            return ""
            
        title = str(title).lower()
        
        # Remove common prefixes (case-insensitive due to .lower() above)
        prefixes = [
            r'^ask hn:', r'^show hn:', r'^poll:', 
            r'^github issue:', r'^problem:', r'^issue:',
            r'^question:', r'^help:', r'^urgent:', r'^psa:'
        ]
        for pattern in prefixes:
            title = re.sub(pattern, '', title).strip()
            
        return title

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Standardizes tags via canonical mapping."""
        if not tags:
            return []
            
        normalized = set()
        for tag in tags:
            if not tag or not isinstance(tag, str): continue
            
            # Basic cleanup
            tag = tag.lower().strip().replace(' ', '-')
            
            # Map to canonical
            tag = self.canonical_tags.get(tag, tag)
            
            if tag:
                normalized.add(tag)
                
        return sorted(list(normalized))

    def _generate_hash(self, text: str) -> str:
        """Generates a SHA-256 hash of the normalized text."""
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _detect_code(self, text: str) -> Tuple[bool, int]:
        """Detects presence and count of code blocks."""
        if not text:
            return False, 0
            
        # Common markdown code block pattern
        blocks = re.findall(r'```', text)
        count = len(blocks) // 2
        
        # Also check for <code> or [code] artifacts if any left
        if count == 0:
            count = len(re.findall(r'\[code\]|<code>', text.lower()))
            
        return count > 0, count

    def _parse_date(self, date_val) -> date:
        """Ensures date is a python date object."""
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, datetime):
            return date_val.date()
        
        if isinstance(date_val, str):
            try:
                # Expecting YYYY-MM-DD
                return datetime.strptime(date_val[:10], '%Y-%m-%d').date()
            except:
                return date.today()
                
        return date.today()
