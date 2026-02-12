"""
Phase 2C: Intelligent Scoring & Matching Algorithms

This module contains refined heuristic and NLP-based algorithms for:
1. Problem Quality Scoring (0-100) - utilizing Readability and Information Density
2. Difficulty Classification - utilizing Topic Complexity
3. Skill-Problem Matching - utilizing Semantic Similarity (placeholder for future vector upgrade)
4. Collaboration Suggestions

All algorithms are deterministic but enhanced with text analysis metrics.
"""

from typing import List, Dict, Tuple
import re
import math

# ============ CONSTANTS & WEIGHTS ============

TOPIC_COMPLEXITY = {
    # High Complexity (Weights 8-10)
    'assembly': 10, 'rust': 9, 'c++': 9, 'kernel': 10, 'distributed-systems': 9,
    'machine-learning': 8, 'ai': 8, 'blockchain': 8, 'cryptography': 10,
    'kubernetes': 8, 'microservices': 8, 'embedded': 9,
    
    # Medium Complexity (Weights 4-7)
    'python': 4, 'javascript': 4, 'react': 5, 'node.js': 5, 'java': 6,
    'sql': 5, 'docker': 6, 'aws': 6, 'azure': 6, 'typescript': 5,
    'go': 6, 'c#': 6, 'swift': 5, 'kotlin': 5, 'android': 6, 'ios': 6,
    
    # Lower Complexity / Entry Level (Weights 1-3)
    'html': 1, 'css': 2, 'bootstrap': 2, 'jquery': 2, 'wordpress': 2,
    'excel': 1, 'bash': 3, 'scripting': 3
}

DEFAULT_COMPLEXITY = 4


# ============ HELPER: NLP METRICS ============

def _count_syllables(word: str) -> int:
    """Simple heuristic for syllable count."""
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for i in range(1, len(word)):
        if word[i] in vowels and word[i - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count

def compute_readability_score(text: str) -> Tuple[float, str]:
    """
    Computes Flesch Reading Ease approximation.
    Returns: (score (0-100 normalized), label)
    Higher is 'better' quality (balanced difficulty).
    """
    if not text:
        return 0.0, "Empty text"
        
    sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
    words = text.split()
    num_words = len(words)
    if num_words < 5:
        return 0.0, "Too short"
        
    num_syllables = sum(_count_syllables(w) for w in words)
    
    # Flesch Reading Ease Formula
    # 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
    score = 206.835 - 1.015 * (num_words / sentences) - 84.6 * (num_syllables / num_words)
    
    # Normalize for our "Quality" metric:
    # 60-70 is standard English. 
    # We want to penalize too simple (<30) or too hard/gibberish (<0 or >100) slightly,
    # but mostly reward clarity.
    
    normalized = min(max(score, 0), 100)
    
    if normalized < 30:
        return 10.0, "Very dense/academic"
    elif normalized < 50:
        return 15.0, "Complex technical"
    elif normalized < 70:
        return 20.0, "Standard clarity" # Optimal
    else:
        return 15.0, "Very simple"

def compute_information_density(text: str) -> float:
    """
    Ratio of unique 'significant' words to total words.
    Higher density implies more specific content.
    """
    words = [w.lower() for w in text.split() if w.isalnum()]
    if not words:
        return 0.0
    
    unique_words = set(words)
    # Simple stopword filter (manual for speed/no deps)
    stops = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
    significant = [w for w in unique_words if w not in stops]
    
    if not words: 
        return 0.0
        
    density = len(significant) / len(words)
    return min(density * 100, 100) # Normalize 0-100


# ============ FEATURE 1: Problem Quality Scoring ============

def score_description_quality(description: str) -> Tuple[int, List[str]]:
    """
    Scores description quality based on NLP metrics (0-40 points).
    """
    if not description:
        return 0, ["No description provided"]
    
    score = 0
    reasons = []
    
    # 1. Readability (Max 20)
    readability_pts, label = compute_readability_score(description)
    score += int(readability_pts)
    reasons.append(f"Readability: {label}")
    
    # 2. Information Density (Max 10) - Reward rich content
    density = compute_information_density(description)
    if density > 40:
        score += 10
        reasons.append("High information density")
    elif density > 20:
        score += 5
        reasons.append("Moderate information density")
        
    # 3. Structure & Formatting (Max 10)
    if '```' in description:
        score += 5
        reasons.append("Includes code blocks")
    if 'Error' in description or 'Exception' in description:
        score += 5
        reasons.append("Includes error details")
        
    return min(score, 40), reasons


def score_technical_depth(suggested_tech: str, tags: List[str]) -> Tuple[int, List[str]]:
    """
    Measures technical complexity using Weighted Topic Scores (0-30 points).
    """
    score = 0
    reasons = []
    
    all_tags = []
    if suggested_tech:
        all_tags.extend([t.strip().lower() for t in suggested_tech.split(',')])
    if tags:
        all_tags.extend([t.lower() for t in tags])
        
    unique_tags = set(all_tags)
    
    if not unique_tags:
        return 5, ["No specific tech tags"]
        
    # Calculate sum of weights
    total_weight = sum(TOPIC_COMPLEXITY.get(t, DEFAULT_COMPLEXITY) for t in unique_tags)
    avg_weight = total_weight / len(unique_tags) if unique_tags else 0
    
    # Base score from complexity
    tech_score = min(total_weight * 1.5, 20)
    score += int(tech_score)
    
    if avg_weight > 7:
        reasons.append("High-complexity tech stack")
    elif avg_weight > 4:
        reasons.append("Standard tech stack")
        
    # Bonus for combination
    if len(unique_tags) >= 3:
        score += 5
        reasons.append("Multi-disciplinary")
    
    # Version specificity
    if any(char.isdigit() for char in suggested_tech or ""):
        score += 5
        reasons.append("Version specific")
        
    return min(score, 30), reasons


def score_reproducibility(description: str, reference_link: str) -> Tuple[int, List[str]]:
    """
    Evaluates how reproducible the problem is (0-20 points).
    """
    score = 0
    reasons = []
    
    # Reference link
    if reference_link and reference_link.startswith('http'):
        score += 10
        reasons.append("Has reference link")
    
    # Reproduction steps
    repro_keywords = ['step', 'setup', 'install', 'run', 'reproduce', 'how to']
    desc_lower = description.lower() if description else ""
    if any(kw in desc_lower for kw in repro_keywords):
        score += 5
        reasons.append("Includes reproduction steps")
    
    # Environment info
    env_keywords = ['version', 'os', 'environment', 'python', 'node', 'npm', 'using']
    if any(kw in desc_lower for kw in env_keywords):
        score += 5
        reasons.append("Specifies environment")
    
    return min(score, 20), reasons

def score_engagement_potential(interested_count: int, views: int) -> Tuple[int, List[str]]:
    """
    Measures community engagement (0-10 points).
    """
    score = 0
    reasons = []
    
    if interested_count > 5:
        score += 10
        reasons.append("High community interest")
    elif interested_count > 0:
        score += 5
        
    return score, reasons


def classify_difficulty_smart(quality_score: int, tech_score: int, avg_topic_weight: float) -> str:
    """
    Classifies problem difficulty using quality and weighted topic complexity.
    """
    # 1. Base difficulty on topic complexity
    if avg_topic_weight >= 8:
        base = "Advanced"
    elif avg_topic_weight <= 3:
        base = "Beginner"
    else:
        base = "Intermediate"
        
    # 2. Adjust based on Quality/Detail 
    # (A very detailed description makes a hard problem easier to approach)
    if base == "Advanced" and quality_score > 80:
        return "Advanced" # Stays advanced, but good quality
        
    if base == "Beginner" and tech_score > 20:
        return "Intermediate" # Simple topic but complex requirements
        
    return base


def estimate_effort_smart(difficulty: str, tech_count: int) -> str:
    """
    Estimates time effort based on difficulty and scope.
    """
    if difficulty == 'Beginner':
        return '1-4 hours'
    elif difficulty == 'Intermediate':
        return '2-5 days' if tech_count < 3 else '1 week'
    else:  # Advanced
        return '2 weeks+'


def compute_problem_quality_score(problem) -> Dict:
    """
    Computes overall quality score and classifications for a problem.
    """
    # Component scores
    desc_score, desc_reasons = score_description_quality(problem.description or "")
    tech_score, tech_reasons = score_technical_depth(problem.suggested_tech or "", problem.tags or [])
    repro_score, repro_reasons = score_reproducibility(problem.description or "", problem.reference_link or "")
    
    interested_count = len(problem.interested_users) if problem.interested_users else 0
    engage_score, engage_reasons = score_engagement_potential(interested_count, problem.views or 0)
    
    # Total quality score
    total_score = desc_score + tech_score + repro_score + engage_score
    total_score = min(total_score, 100)
    
    # Metrics for difficulty
    all_tags = []
    if problem.suggested_tech:
        all_tags.extend([t.strip().lower() for t in problem.suggested_tech.split(',')])
    unique_tags = set(all_tags)
    total_weight = sum(TOPIC_COMPLEXITY.get(t, DEFAULT_COMPLEXITY) for t in unique_tags)
    avg_weight = total_weight / len(unique_tags) if unique_tags else DEFAULT_COMPLEXITY
    
    # Classifications
    difficulty = classify_difficulty_smart(total_score, tech_score, avg_weight)
    effort = estimate_effort_smart(difficulty, len(unique_tags))
    
    return {
        "quality_score": total_score,
        "difficulty": difficulty,
        "estimated_effort": effort,
        "breakdown": {
            "description_quality": {"score": desc_score, "max": 40, "reasons": desc_reasons},
            "technical_depth": {"score": tech_score, "max": 30, "reasons": tech_reasons},
            "reproducibility": {"score": repro_score, "max": 20, "reasons": repro_reasons},
            "engagement": {"score": engage_score, "max": 10, "reasons": engage_reasons}
        }
    }

# ============ COMPATIBILITY FOR OLD EXPORTS ============
# These allow main.py to seamlessly import

def calculate_problem_difficulty(problem) -> str:
    """Alias for direct difficulty calculation"""
    res = compute_problem_quality_score(problem)
    return res['difficulty']


# ============ FEATURE 2: User Matching (Unchanged for now) ============
# ... (Keeping existing matching logic, but it uses the weights implicitly if we updated it)
# For brevity in this update, we retain the robust logic from previous version below 
# but ensure it imports clean. 

def calculate_skill_match(user_skills: List[str], problem_tech: str) -> Tuple[int, List[str]]:
    if not user_skills: return 0, ["No skills listed"]
    problem_techs = [t.strip().lower() for t in problem_tech.split(',') if t.strip()]
    if not problem_techs: return 10, ["General problem"]
    user_skills_lower = [s.lower() for s in user_skills]
    matches = 0
    for tech in problem_techs:
        if any(skill in tech or tech in skill for skill in user_skills_lower):
            matches += 1
    match_ratio = matches / len(problem_techs)
    score = int(match_ratio * 40)
    reasons = []
    if match_ratio >= 0.5: reasons.append(f"Strong match ({matches}/{len(problem_techs)} techs)")
    elif match_ratio > 0: reasons.append(f"Partial match")
    return score, reasons

def calculate_difficulty_match(user_level: str, user_pref: str, problem_difficulty: str) -> Tuple[int, List[str]]:
    levels = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2}
    pref_idx = levels.get(user_pref, 1)
    prob_idx = levels.get(problem_difficulty, 1)
    if pref_idx == prob_idx: return 20, ["Perfect difficulty match"]
    elif abs(pref_idx - prob_idx) == 1: return 10, ["Close difficulty match"]
    return 5, ["Challenging difficulty"]

def calculate_interest_match(user_interests: List[str], problem_tags: List[str], problem_desc: str) -> Tuple[int, List[str]]:
    if not user_interests: return 10, []
    score = 0
    matched = []
    for interest in user_interests:
        if problem_tags and any(interest.lower() in tag.lower() for tag in problem_tags):
            score += 10
            matched.append(interest)
        elif problem_desc and interest.lower() in problem_desc.lower():
            score += 5
    return min(score, 20), [f"Matches: {', '.join(matched[:2])}"] if matched else []

def calculate_novelty_score(user, problem) -> Tuple[int, List[str]]:
    if user in problem.interested_users: return 5, ["Already interested"]
    return 10, ["New discovery"]

def compute_match_score(user, problem) -> Dict:
    skill_score, skill_reasons = calculate_skill_match(user.skills or [], problem.suggested_tech or "")
    diff = calculate_problem_difficulty(problem) # Use the smart calculator!
    diff_score, diff_reasons = calculate_difficulty_match(
        user.experience_level or "Intermediate",
        user.preferred_difficulty or "Intermediate",
        diff
    )
    interest_score, interest_reasons = calculate_interest_match(
        user.interests or [], problem.tags or [], problem.description or ""
    )
    novelty_score, novelty_reasons = calculate_novelty_score(user, problem)
    
    total = skill_score + diff_score + interest_score + novelty_score
    return {
        "match_score": total,
        "reasons": skill_reasons + diff_reasons + interest_reasons + novelty_reasons,
        "breakdown": {"skill": skill_score, "difficulty": diff_score, "interest": interest_score}
    }





# ============ FEATURE 3: Collaboration Suggestions ============

def calculate_skill_complementarity(user_a_skills: List[str], user_b_skills: List[str], problem_tech: str) -> Tuple[int, List[str]]:
    """
    Scores how well two users' skills complement each other (0-35 points).
    
    Best scenario: Together they cover all problem techs
    """
    if not user_a_skills or not user_b_skills:
        return 10, ["Limited skill information"]
    
    problem_techs = set(t.strip().lower() for t in problem_tech.split(',') if t.strip())
    if not problem_techs:
        return 15, ["General collaboration"]
    
    a_skills_lower = [s.lower() for s in user_a_skills]
    b_skills_lower = [s.lower() for s in user_b_skills]
    
    # What each user covers
    a_matches = {tech for tech in problem_techs if any(skill in tech or tech in skill for skill in a_skills_lower)}
    b_matches = {tech for tech in problem_techs if any(skill in tech or tech in skill for skill in b_skills_lower)}
    
    # Combined coverage
    combined_coverage = len(a_matches | b_matches) / len(problem_techs)
    
    # Unique contribution from user B
    unique_contribution = len(b_matches - a_matches) / len(problem_techs) if problem_techs else 0
    
    score = int((combined_coverage * 25) + (unique_contribution * 10))
    
    reasons = []
    if combined_coverage >= 0.8:
        reasons.append("Comprehensive skill coverage together")
    if unique_contribution > 0.3:
        reasons.append("Brings complementary skills")
    
    return min(score, 35), reasons


def calculate_experience_balance(user_a_level: str, user_b_level: str, problem_diff: str) -> Tuple[int, List[str]]:
    """
    Evaluates experience balance (0-20 points).
    
    Ideal: Mix of levels OR both match problem
    """
    levels_map = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2}
    
    a_idx = levels_map.get(user_a_level, 1)
    b_idx = levels_map.get(user_b_level, 1)
    prob_idx = levels_map.get(problem_diff, 1)
    
    reasons = []
    
    # Both match problem
    if a_idx == prob_idx and b_idx == prob_idx:
        score = 20
        reasons.append("Both match problem difficulty")
    # One matches, one helps
    elif (a_idx == prob_idx and abs(b_idx - prob_idx) <= 1) or \
         (b_idx == prob_idx and abs(a_idx - prob_idx) <= 1):
        score = 15
        reasons.append("Good experience balance")
    # Mentorship opportunity
    elif abs(a_idx - b_idx) >= 1:
        score = 12
        reasons.append("Mentorship opportunity")
    else:
        score = 8
    
    return score, reasons


def calculate_activity_compatibility(user_a_activity: int, user_b_activity: int) -> Tuple[int, List[str]]:
    """
    Checks if both users are active (0-25 points).
    
    Both active → Better collaboration
    """
    avg_activity = (user_a_activity + user_b_activity) / 2
    activity_gap = abs(user_a_activity - user_b_activity)
    
    score = int(avg_activity * 0.2)  # Max 20 from average
    
    reasons = []
    if avg_activity > 70:
        reasons.append("Both highly active")
    elif avg_activity > 40:
        reasons.append("Good activity levels")
    
    # Penalty for large gap
    if activity_gap > 40:
        score -= 10
        reasons.append("Activity mismatch")
    
    return max(min(score, 25), 0), reasons


def calculate_past_success(user_a, user_b) -> Tuple[int, List[str]]:
    """
    Checks past collaboration history (0-20 points).
    
    First time: Neutral (10 pts)
    Past collaboration: Bonus points
    """
    # Check shared groups
    a_groups = set(user_a.joined_collaboration_groups) if hasattr(user_a, 'joined_collaboration_groups') else set()
    b_groups = set(user_b.joined_collaboration_groups) if hasattr(user_b, 'joined_collaboration_groups') else set()
    
    shared_groups = a_groups & b_groups
    
    reasons = []
    if len(shared_groups) > 0:
        score = min(20, 10 + len(shared_groups) * 5)
        reasons.append(f"Past collaborations ({len(shared_groups)})")
    else:
        score = 10  # Neutral for new pairs
    
    return score, reasons


def compute_compatibility_score(user_a, user_b, problem) -> Dict:
    """
    Computes compatibility score between two users for a problem.
    
    Returns dict with:
    - compatibility_score (0-100)
    - reasons (human-readable)
    - breakdown (component scores)
    """
    skill_comp, skill_reasons = calculate_skill_complementarity(
        user_a.skills or [],
        user_b.skills or [],
        problem.suggested_tech or ""
    )
    exp_balance, exp_reasons = calculate_experience_balance(
        user_a.experience_level or "Intermediate",
        user_b.experience_level or "Intermediate",
        problem.difficulty or "Intermediate"
    )
    activity_comp, activity_reasons = calculate_activity_compatibility(
        user_a.activity_score or 50,
        user_b.activity_score or 50
    )
    past_success, past_reasons = calculate_past_success(user_a, user_b)
    
    total_score = skill_comp + exp_balance + activity_comp + past_success
    
    all_reasons = skill_reasons + exp_reasons + activity_reasons + past_reasons
    
    return {
        "compatibility_score": total_score,
        "reasons": all_reasons,
        "breakdown": {
            "skill_complementarity": skill_comp,
            "experience_balance": exp_balance,
            "activity_compatibility": activity_comp,
            "past_success": past_success
        }
    }


# ============ FEATURE 4: Classification & Explanation Helpers ============

def classify_solution_type(description: str, tags: List[str] = None) -> str:
    """
    Determine if problem requires software, hardware, or hybrid solution.
    Centralized logic used by all scrapers.
    """
    text_lower = (description or "").lower()
    tags_lower = " ".join(tags or []).lower()
    combined = text_lower + " " + tags_lower
    
    # Hardware keywords
    hardware_keywords = [
        'arduino', 'raspberry pi', 'sensor', 'embedded', 'firmware',
        'microcontroller', 'circuit', 'hardware', 'fpga', 'esp32', 'esp8266',
        'physical device'
    ]
    
    # Hybrid keywords
    hybrid_keywords = [
        'robotics', 'robot', 'drone', '3d print', 'cnc', 'automation',
        'iot device', 'smart home', 'wearable'
    ]
    
    has_hardware = any(kw in combined for kw in hardware_keywords)
    has_hybrid = any(kw in combined for kw in hybrid_keywords)
    
    if has_hybrid:
        return 'hybrid'
    elif has_hardware:
        return 'hardware'
    else:
        return 'software'


def generate_humanized_explanation(title: str, body: str) -> str:
    """
    Generate a simple, human-readable explanation of the problem.
    Extracts first 2-3 sentences or creates a shortened version.
    """
    if not body:
        return title
        
    # Clean the body (remove code blocks, URLs, excessive whitespace)
    clean_body = re.sub(r'```[\s\S]*?```', '', body)  # Remove code blocks
    clean_body = re.sub(r'http[s]?://\S+', '', clean_body)  # Remove URLs
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()  # Normalize whitespace
    
    # Combine title and body
    full_text = f"{title}. {clean_body}"
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', full_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Take first 2-3 sentences, max 250 chars
    explanation = '. '.join(sentences[:3])
    
    if len(explanation) > 250:
        explanation = explanation[:247] + '...'
    
    return explanation if explanation else title


def is_tech_solvable(title: str, body: str) -> bool:
    """
    Filter to determine if a post/issue is a solvable technical problem.
    Returns True if it looks like a real problem, False if noise/discussion.
    """
    combined = (f"{title} {body}").lower()
    
    # Positive signals: Problem-oriented keywords
    problem_keywords = [
        'how to', 'how do i', 'error', 'bug', 'issue', 'help', 'problem',
        'fail', 'crash', 'not working', 'difficulty', 'stuck', 'fix',
        'implement', 'design', 'architecture', 'best way to', 'question'
    ]
    
    # Negative signals: Too short, spam, or meta-discussion
    if len(combined) < 50:
        return False
        
    noise_keywords = [
        '[meta]', '[offtopic]', 'congratulations', 'hiring', 'job', 
        'career advice', 'thank you', 'thanks', 'just want to say'
    ]
    
    if any(nk in combined for nk in noise_keywords):
        return False
        
    return any(pk in combined for pk in problem_keywords)


def suggest_tech(text: str) -> str:
    """
    Suggest technologies based on keyword matching with TOPIC_COMPLEXITY.
    Returns a comma-separated string of identified techs.
    """
    text_lower = text.lower()
    found_techs = []
    
    for tech in TOPIC_COMPLEXITY.keys():
        # Match as whole word or with standard delimiters
        pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, text_lower):
            found_techs.append(tech.capitalize())
            
    # Also check common variants/synonyms if needed
    if 'react' in text_lower and 'React' not in found_techs:
        found_techs.append('React')
        
    return ', '.join(found_techs[:5]) if found_techs else 'General Tech'
