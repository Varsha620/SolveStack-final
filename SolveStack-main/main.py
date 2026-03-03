from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from models import User, Problem, CollaborationGroup, CollaborationRequest, Base, group_members
from database import engine, get_db
from schemas import (
    UserCreate, UserResponse, Token,
    ProblemResponse, ProblemDetailResponse,
    InterestRequest, InterestResponse,
    CollaborationRequestCreate, CollaborationActionRequest,
    CollaborationRequestResponse, CollaborationStatusResponse, CollaborationGroupInfo,
    ScrapeRequest, ScrapeResponse, ScrapeAllResponse,
    HybridSearchResponse, SemanticSearchResponse, IntentAwareSearchResponse,
    ShelfResponse, ImpactExplanation, ShelfAnalytics
)
from search_service import get_search_service
from impact_explanation_service import get_explanation_service
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from cleaning_layer import DataCleaner


load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SolveStack API",
    description="Crowdsourced tech problems platform API",
    version="1.0.0"
)

# CORS configuration
# CORS configuration
origins = ["*"]  # Allow all origins for development to fix IP-based access issues

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Authentication Endpoints ============

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: Valid email address (unique)
    - **username**: Username (3-50 chars, unique)
    - **password**: Password (min 6 chars)
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token, tags=["Authentication"])
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and receive JWT access token
    
    - **username**: Email address (OAuth2 uses 'username' field for email)
    - **password**: User password
    """
    # Find user by email (OAuth2PasswordRequestForm uses 'username' field for email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse, tags=["Authentication"])
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information (requires authentication)"""
    from models import problem_interests, group_members
    from sqlalchemy import func
    
    # Interested count - Using more robust query
    interested_count = db.query(func.count(problem_interests.c.user_id)).filter(
        problem_interests.c.user_id == current_user.id
    ).scalar() or 0
    
    # Squads count
    squads_count = db.query(func.count(group_members.c.user_id)).filter(
        group_members.c.user_id == current_user.id
    ).scalar() or 0
    
    print(f">>> [PROFILE DEBUG] Request for User ID: {current_user.id} ({current_user.username})")
    print(f">>> [PROFILE DEBUG] Database found - Interests: {interested_count}, Squads: {squads_count}")
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "is_premium": current_user.is_premium,
        "interested_count": interested_count,
        "squads_count": squads_count
    }


@app.get("/search/hybrid", response_model=List[HybridSearchResponse], tags=["Search"])
def hybrid_search(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Perform a hybrid search (Semantic + Keyword + Tags)
    
    - **query**: Search string
    - **limit**: Maximum results to return
    """
    search_service = get_search_service()
    
    # We'll just pass the query as query_text. 
    # If the user wants to extract tags, we'd need another layer, 
    # but the request specifically says: query=...
    results = search_service.search(db, query_text=query, limit=limit)
    
    return [
        {
            "ps_id": p.ps_id,
            "title": p.title,
            "description": p.description,
            "semantic_score": p.search_scores["semantic"],
            "keyword_score": p.search_scores["keyword"],
            "tag_score": p.search_scores["tag"],
            "final_score": p.search_scores["final"]
        } for p in results
    ]

@app.get("/search", response_model=IntentAwareSearchResponse, tags=["Search"])
def search(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Perform a Google-style intent-aware search.
    - **query**: Natural language or keyword query
    - **limit**: Maximum results to return
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
        
    search_service = get_search_service()
    
    try:
        results, metadata = search_service.intent_aware_search(
            db, 
            query=query, 
            limit=limit
        )
        
        return {
            "query": query,
            "results": [
                {
                    "ps_id": p.ps_id,
                    "title": p.title,
                    "description": p.description,
                    "tags": p.tags or [],
                    "scores": p.search_scores
                } for p in results
            ],
            "metadata": metadata
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/search/semantic", response_model=SemanticSearchResponse, tags=["Search"])
def semantic_search(
    query: str,
    limit: int = 10,
    min_score: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    Perform a pure research-grade semantic search (normalized).
    
    - **query**: Search string (max 500 chars)
    - **limit**: Maximum results to return
    - **min_score**: Minimum similarity threshold [0-1]
    """
    # STEP 5: Safety & Validation
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
        
    if len(query) > 500:
        query = query[:500]
        
    search_service = get_search_service()
    
    try:
        results, metadata = search_service.search_semantic(
            db, 
            query=query, 
            limit=limit, 
            min_score=min_score
        )
        
        if "error" in metadata:
            raise HTTPException(status_code=500, detail=metadata["error"])
            
        return {
            "query": query,
            "results": [
                {
                    "ps_id": p.ps_id,
                    "title": p.title,
                    "description": p.description,
                    "tags": p.tags or [],
                    "semantic_score": p.search_scores["semantic"]
                } for p in results
            ],
            "metadata": metadata
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@app.get("/shelf", response_model=ShelfResponse, tags=["Shelf Intelligence"])
def get_shelf(
    mode: str = "explore",
    sort_by: str = "impact",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Access the intelligent Problem Shelf with curated modes.
    - **mode**: explore, production, architecture, high-cognitive
    - **sort_by**: impact, depth, recency
    """
    from sqlalchemy import cast, JSON, func
    query = db.query(Problem)
    
    # Modes
    if mode == "production":
        query = query.filter(Problem.industry_impact_score > 0.6, Problem.signal_quality_score > 0.6)
    elif mode == "architecture":
        query = query.filter(Problem.technical_depth_score > 0.7)
        # Multi-domain: problems with at least 2 tags
        query = query.filter(func.json_array_length(cast(Problem.tags, JSON)) >= 2)
    elif mode == "high-cognitive":
        query = query.filter(Problem.cognitive_complexity_score > 0.7)
    
    # Sorting
    if sort_by == "impact":
        query = query.order_by(Problem.engineering_impact_score.desc())
    elif sort_by == "depth":
        query = query.order_by(Problem.technical_depth_score.desc())
    else:
        # Default to recency if not specified or fallback
        query = query.order_by(Problem.scraped_at.desc())
        
    results = query.limit(limit).all()
    
    return {
        "mode": mode,
        "total_found": len(results),
        "results": [
            {
                "id": p.ps_id,
                "title": p.title,
                "engineering_impact_score": p.engineering_impact_score,
                "technical_depth_score": p.technical_depth_score,
                "industry_impact_score": p.industry_impact_score,
                "cognitive_complexity_score": p.cognitive_complexity_score,
                "signal_quality_score": p.signal_quality_score,
                "tags": p.tags or []
            } for p in results
        ]
    }


@app.get("/shelf/{problem_id}/explain", response_model=ImpactExplanation, tags=["Shelf Intelligence"])
def explain_impact(
    problem_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a natural language explanation for why a problem ranks high.
    """
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    explanation_service = get_explanation_service()
    return explanation_service.explain_score(problem)


@app.get("/analytics/shelf", response_model=ShelfAnalytics, tags=["Shelf Intelligence"])
def get_shelf_analytics(db: Session = Depends(get_db)):
    """
    Global analytics for the Intelligent Shelf.
    """
    from sqlalchemy import func
    total = db.query(Problem).count()
    if total == 0:
        return {
            "total_analyzed": 0, "low_signal_percentage": 0, "avg_impact_score": 0,
            "top_impact_problems": [], "eis_distribution": []
        }
    
    avg_impact = db.query(func.avg(Problem.engineering_impact_score)).scalar()
    low_signal = db.query(Problem).filter(Problem.signal_quality_score < 0.4).count()
    
    top_5 = db.query(Problem).order_by(Problem.engineering_impact_score.desc()).limit(5).all()
    
    # Distribution
    distribution = []
    buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    for start, end in buckets:
        count = db.query(Problem).filter(
            Problem.engineering_impact_score >= start,
            Problem.engineering_impact_score < (end if end < 100 else 101)
        ).count()
        distribution.append({"bucket": f"{start}-{end}", "count": count})
        
    return {
        "total_analyzed": total,
        "low_signal_percentage": round((low_signal / total) * 100, 2),
        "avg_impact_score": round(avg_impact or 0, 2),
        "top_impact_problems": [
            {"id": p.ps_id, "title": p.title, "score": p.engineering_impact_score}
            for p in top_5
        ],
        "eis_distribution": distribution
    }


# ============ Problem Endpoints ============

def _map_problem_to_response(problem: Problem, current_user: Optional[User] = None) -> dict:
    """Helper to map a Problem model to a unified dictionary response"""
    return {
        "ps_id": problem.ps_id,
        "title": problem.title,
        "description": problem.description,
        "source": problem.source,
        "source_id": problem.source_id,
        "date": problem.date,
        "suggested_tech": problem.suggested_tech,
        "author_name": problem.author_name,
        "author_id": problem.author_id,
        "reference_link": problem.reference_link,
        "tags": problem.tags or [],
        "scraped_at": problem.scraped_at,
        "difficulty_score": problem.difficulty_score or 0.0,
        "difficulty_level": problem.difficulty_level or 0,
        "upvotes": problem.upvotes or 0,
        "downvotes": problem.downvotes or 0,
        "comment_count": problem.comment_count or 0,
        "engagement_score": problem.engagement_score or 0.0,
        "text_length": problem.text_length or 0,
        "interested_count": len(problem.interested_users),
        "is_interested": current_user in problem.interested_users if current_user else False,
        # New cleaning/metadata fields
        "raw_title": problem.raw_title,
        "raw_tags": problem.raw_tags,
        "normalized_title": problem.normalized_title,
        "title_hash": problem.title_hash,
        "word_count": problem.word_count,
        "has_code_block": problem.has_code_block,
        "num_code_blocks": problem.num_code_blocks,
        "clean_version": problem.clean_version,
        # Engineering Impact Scoring (EIS)
        "technical_depth_score": problem.technical_depth_score or 0.0,
        "industry_impact_score": problem.industry_impact_score or 0.0,
        "cognitive_complexity_score": problem.cognitive_complexity_score or 0.0,
        "signal_quality_score": problem.signal_quality_score or 0.0,
        "engineering_impact_score": problem.engineering_impact_score or 0.0
    }

@app.get("/problems", response_model=List[ProblemResponse], tags=["Problems"])
def get_problems(
    skip: int = 0,
    limit: int = 100,
    tech: str = None,
    source: str = None,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Get all problems with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **tech**: Filter by technology (e.g., 'python', 'react')
    - **source**: Filter by source platform (e.g., 'reddit', 'github')
    """
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    query = db.query(Problem)
    
    # Apply filters
    if tech:
        query = query.filter(Problem.suggested_tech.contains(tech))
    if source:
        query = query.filter(Problem.source.contains(source))
    
    problems = query.order_by(Problem.scraped_at.desc()).offset(skip).limit(limit).all()
    
    return [_map_problem_to_response(p, current_user) for p in problems]


@app.get("/problems/trending", response_model=List[ProblemResponse], tags=["Problems"])
def get_trending_problems(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Get the top 15 most liked problems
    
    Returns problems with the highest 'interested_count' first.
    """
    from models import problem_interests
    from sqlalchemy import func
    
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    # We want to sort by the number of interested users.
    # A subquery counting interests per problem is efficient.
    interest_counts = db.query(
        problem_interests.c.problem_id,
        func.count(problem_interests.c.user_id).label('count')
    ).group_by(problem_interests.c.problem_id).subquery()

    # Join problems with the interest counts subquery
    problems = db.query(Problem).outerjoin(
        interest_counts, Problem.ps_id == interest_counts.c.problem_id
    ).order_by(
        func.coalesce(interest_counts.c.count, 0).desc(), 
        Problem.scraped_at.desc()
    ).limit(15).all()
    
    return [_map_problem_to_response(p, current_user) for p in problems]


@app.get("/problems/{problem_id}", response_model=ProblemDetailResponse, tags=["Problems"])
def get_problem_detail(
    problem_id: int, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get detailed information about a specific problem"""
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    response = _map_problem_to_response(problem, current_user)
    response["interested_users"] = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at,
            "is_premium": u.is_premium
        } for u in problem.interested_users
    ]
    
    return response


@app.post("/scrape", response_model=ScrapeResponse, tags=["Admin"])
def trigger_scrape(
    request: ScrapeRequest = ScrapeRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger scraping from configured platforms (admin only)
    """
    from scrapers.reddit_scraper import scrape_reddit
    from scrapers import scrape_github
    
    reddit_count = 0
    github_count = 0
    
    try:
        if "reddit" in request.platforms:
            reddit_problems = scrape_reddit(limit=request.limit)
            # Use local helper or store_problems_in_db logic
            # For simplicity, similar to scrape_all_sources
            
            # Since trigger_scrape is simpler and older, we'll keep it simple but correct references
            def quick_store(problems):
                count = 0
                cleaner = DataCleaner()
                for p_raw in problems:
                    try:
                        # 1. Clean and enrich
                        p_data = cleaner.clean_problem(p_raw)
                        
                        # 2. Check for duplicate link
                        existing = db.query(Problem).filter(
                            Problem.reference_link == p_data['reference_link']
                        ).first()
                        if existing: continue
                        
                        # 3. Check for duplicate hash
                        existing_hash = db.query(Problem).filter(
                            Problem.title_hash == p_data['title_hash']
                        ).first()
                        if existing_hash: continue

                        new_p = Problem(**p_data)
                        db.add(new_p)
                        db.commit()
                        count += 1
                    except Exception as e:
                        print(f"Quick store error: {e}")
                        db.rollback()
                        continue
                return count

            reddit_count = quick_store(reddit_problems)
        
        if "github" in request.platforms:
            github_problems = scrape_github(limit=request.limit)
            github_count = quick_store(github_problems)
        
        total = reddit_count + github_count
        
        return {
            "message": f"Successfully scraped {total} problems",
            "total_scraped": total,
            "reddit_count": reddit_count,
            "github_count": github_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@app.post("/scrape/all", response_model=ScrapeAllResponse, tags=["Admin"])
def scrape_all_sources(db: Session = Depends(get_db)):
    """
    Unified scraper: Fetch problems from all sources (GitHub, Stack Overflow, Hacker News).
    
    Behavior:
    - TARGET: 30 total problems per run
    - Quota redistribution: If one platform returns fewer results, redistributes to others
    - Continues fetching until quota met or all sources exhausted
    - De-duplicates based on:
      1. reference_link (unique constraint)
      2. source + source_id combination
      3. Title similarity within same source (>85% match)
    """
    from scrapers import scrape_github, scrape_stackoverflow, scrape_hackernews
    from sqlalchemy.exc import IntegrityError
    from difflib import SequenceMatcher
    
    # In-memory session-level dedupe
    seen_hashes = set()
    cleaner = DataCleaner()
    
    total_processed = 0
    total_cleaned = 0
    total_deduped = 0
    records_with_code = 0
    
    source_results = {
        "github": 0,
        "stackoverflow": 0,
        "hackernews": 0,
        "reddit": 0
    }

    def is_duplicate(cleaned_data: dict, db: Session) -> bool:
        # Layer 1: Reference link
        existing_link = db.query(Problem).filter(
            Problem.reference_link == cleaned_data['reference_link']
        ).first()
        if existing_link: return True
        
        # Layer 2: Title Hash
        existing_hash = db.query(Problem).filter(
            Problem.title_hash == cleaned_data['title_hash']
        ).first()
        if existing_hash: return True
        
        # Layer 3: Session check
        if cleaned_data['title_hash'] in seen_hashes: return True
        
        return False

    def insert_problems(problems_raw, source_key):
        inserted = 0
        deduped = 0
        nonlocal total_cleaned, records_with_code
        
        for p_raw in problems_raw:
            try:
                # 1. Clean
                cleaned_p = cleaner.clean_problem(p_raw)
                total_cleaned += 1
                if cleaned_p['has_code_block']:
                    records_with_code += 1
                
                # 2. Deduplicate
                if is_duplicate(cleaned_p, db):
                    deduped += 1
                    continue
                
                # 3. Insert
                new_problem = Problem(**cleaned_p)
                db.add(new_problem)
                db.commit()
                
                seen_hashes.add(cleaned_p['title_hash'])
                inserted += 1
            except Exception as e:
                print(f"Insertion error ({source_key}): {e}")
                db.rollback()
                continue
        
        return inserted, deduped
    
    # QUOTA ENFORCEMENT CONSTANTS
    TARGET_TOTAL = 30
    INITIAL_PER_SOURCE = 10
    
    github_count = 0
    stackoverflow_count = 0
    hackernews_count = 0
    total_duplicates = 0
    
    github_fetched = 0
    stackoverflow_fetched = 0
    hackernews_fetched = 0
    
    try:
        print("\n" + "=" * 70)
        print("🚀 MULTI-SOURCE SCRAPING WITH QUOTA ENFORCEMENT")
        print("=" * 70)
        print(f"🎯 TARGET: {TARGET_TOTAL} total problems")
        print(f"📊 STRATEGY: {INITIAL_PER_SOURCE} per source, redistribute if needed")
        print("=" * 70)
        
        # PHASE 1: Initial scraping (10 from each source)
        print(f"\n📥 PHASE 1: Initial Scraping ({INITIAL_PER_SOURCE} per source)")
        print("-" * 70)
        
        # Scrape GitHub
        print(f"\n[1/3] GitHub...")
        try:
            github_problems = scrape_github(limit=INITIAL_PER_SOURCE)
            github_fetched = len(github_problems)
            github_count, github_dups = insert_problems(github_problems, "github")
            total_duplicates += github_dups
            source_results["github"] = github_count
            print(f"  ✅ GitHub: {github_count} inserted, {github_dups} duplicates")
        except Exception as e:
            print(f"  ❌ GitHub scraping failed: {str(e)[:100]}")
            github_problems = []
        
        # Scrape Stack Overflow
        print(f"\n[2/3] Stack Overflow...")
        try:
            stackoverflow_problems = scrape_stackoverflow(limit=INITIAL_PER_SOURCE)
            stackoverflow_fetched = len(stackoverflow_problems)
            stackoverflow_count, so_dups = insert_problems(stackoverflow_problems, "stackoverflow")
            total_duplicates += so_dups
            source_results["stackoverflow"] = stackoverflow_count
            print(f"  ✅ Stack Overflow: {stackoverflow_count} inserted, {so_dups} duplicates")
        except Exception as e:
            print(f"  ❌ Stack Overflow scraping failed: {str(e)[:100]}")
            stackoverflow_problems = []
        
        # Scrape Hacker News
        print(f"\n[3/3] Hacker News...")
        try:
            hackernews_problems = scrape_hackernews(limit=INITIAL_PER_SOURCE)
            hackernews_fetched = len(hackernews_problems)
            hackernews_count, hn_dups = insert_problems(hackernews_problems, "hackernews")
            total_duplicates += hn_dups
            source_results["hackernews"] = hackernews_count
            print(f"  ✅ Hacker News: {hackernews_count} inserted, {hn_dups} duplicates")
        except Exception as e:
            print(f"  ❌ Hacker News scraping failed: {str(e)[:100]}")
            hackernews_problems = []
        
        # Calculate current total
        current_total = github_count + stackoverflow_count + hackernews_count
        
        print(f"\n📊 Phase 1 Complete: {current_total}/{TARGET_TOTAL} problems added")
        
        # PHASE 2: Quota Redistribution (if needed)
        if current_total < TARGET_TOTAL:
            shortage = TARGET_TOTAL - current_total
            print(f"\n📈 PHASE 2: Quota Redistribution")
            print(f"  Shortage: {shortage} problems")
            print(f"  Redistributing to all sources...")
            print("-" * 70)
            
            # Try to fill quota by fetching more from each source
            attempts = 0
            max_attempts = 3  # Prevent infinite loops
            
            while current_total < TARGET_TOTAL and attempts < max_attempts:
                attempts += 1
                additional_per_source = max(5, (shortage // 3) + 1)
                
                print(f"\n  Attempt {attempts}: Fetching {additional_per_source} more from each source...")
                
                # Additional GitHub
                if current_total < TARGET_TOTAL:
                    try:
                        extra_github = scrape_github(limit=additional_per_source)
                        if extra_github:
                            extra_count, extra_dups = insert_problems(extra_github, "github")
                            github_count += extra_count
                            source_results["github"] = github_count
                            github_fetched += len(extra_github)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    GitHub: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Stack Overflow
                if current_total < TARGET_TOTAL:
                    try:
                        extra_so = scrape_stackoverflow(limit=additional_per_source)
                        if extra_so:
                            extra_count, extra_dups = insert_problems(extra_so, "stackoverflow")
                            stackoverflow_count += extra_count
                            source_results["stackoverflow"] = stackoverflow_count
                            stackoverflow_fetched += len(extra_so)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    Stack Overflow: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Hacker News
                if current_total < TARGET_TOTAL:
                    try:
                        extra_hn = scrape_hackernews(limit=additional_per_source)
                        if extra_hn:
                            extra_count, extra_dups = insert_problems(extra_hn, "hackernews")
                            hackernews_count += extra_count
                            source_results["hackernews"] = hackernews_count
                            hackernews_fetched += len(extra_hn)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    Hacker News: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                shortage = TARGET_TOTAL - current_total
                if shortage <= 0:
                    break
        
        # FINAL SUMMARY
        print(f"\n" + "=" * 70)
        print(f"✅ SCRAPING COMPLETE")
        print("=" * 70)
        print(f"\n📊 TOTALS:")
        print(f"  Problems Added: {current_total}/{TARGET_TOTAL} ({(current_total/TARGET_TOTAL*100):.1f}%)")
        print(f"  Total Fetched: {github_fetched + stackoverflow_fetched + hackernews_fetched}")
        print(f"  Duplicates Skipped: {total_duplicates}")
        
        print(f"\n📈 BY SOURCE:")
        print(f"  GitHub:         {github_count:>3} added ({github_fetched} fetched)")
        print(f"  Stack Overflow: {stackoverflow_count:>3} added ({stackoverflow_fetched} fetched)")
        print(f"  Hacker News:    {hackernews_count:>3} added ({hackernews_fetched} fetched)")
        print("=" * 70 + "\n")
        
        return {
            "message": f"Successfully scraped {current_total} new problems ({total_duplicates} duplicates skipped)",
            "total_scraped": current_total,
            "total_fetched": github_fetched + stackoverflow_fetched + hackernews_fetched,
            "total_cleaned": total_cleaned,
            "records_with_code": records_with_code,
            "github_count": github_count,
            "github_fetched": github_fetched,
            "stackoverflow_count": stackoverflow_count,
            "stackoverflow_fetched": stackoverflow_fetched,
            "hackernews_count": hackernews_count,
            "hackernews_fetched": hackernews_fetched,
            "duplicates_skipped": total_duplicates,
            "target_per_source": INITIAL_PER_SOURCE,
            "target_total": TARGET_TOTAL
        }
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-source scraping failed: {str(e)}"
        )



# ============ Interest & Collaboration Endpoints ============

@app.post("/interest", response_model=InterestResponse, tags=["Collaboration"])
def mark_interest(
    request: InterestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark interest in a problem (requires authentication)
    
    - **problem_id**: ID of the problem to mark interest in
    """
    from models import problem_interests
    from sqlalchemy import select, delete, insert, func
    
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == request.problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if user already marked interest using direct query
    stmt = select(problem_interests).where(
        problem_interests.c.user_id == current_user.id,
        problem_interests.c.problem_id == problem.ps_id
    )
    existing = db.execute(stmt).first()
    
    if existing:
        # Get count
        count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
        total = db.execute(count_stmt).scalar() or 0
        return {
            "message": "Already marked as interested",
            "total_interested": total
        }
    
    # Add interest direct insert
    db.execute(insert(problem_interests).values(user_id=current_user.id, problem_id=problem.ps_id))
    db.commit()
    
    # Get total count for problem
    count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
    total = db.execute(count_stmt).scalar() or 0
    
    print(f"MARK INTEREST SUCCESS: User {current_user.id} -> Problem {problem.ps_id}. New Total: {total}")
    
    return {
        "message": "Interest marked successfully",
        "total_interested": total
    }


@app.delete("/interest/{problem_id}", tags=["Collaboration"])
def remove_interest(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove interest from a problem"""
    from models import problem_interests
    from sqlalchemy import delete, select, func
    
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Direct delete
    stmt = delete(problem_interests).where(
        problem_interests.c.user_id == current_user.id,
        problem_interests.c.problem_id == problem.ps_id
    )
    db.execute(stmt)
    db.commit()
    
    # Get total count for problem after deletion
    count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
    total = db.execute(count_stmt).scalar() or 0
    
    print(f"REMOVE INTEREST: User {current_user.id} -> Problem {problem.ps_id}. New Total: {total}")
    
    return {
        "message": "Interest removed successfully",
        "total_interested": total
    }


@app.get("/me/interests", response_model=List[ProblemResponse], tags=["Authentication"])
def get_user_interests(
    current_user: User = Depends(get_current_user)
):
    """Get the list of problems the current user is interested in"""
    result = []
    for problem in current_user.interested_problems:
        result.append(_map_problem_to_response(problem, current_user))
    
    return result


# ============ Collaboration Endpoints (Phase 2B) ============

# Constant for minimum group size
MIN_GROUP_SIZE = 2

def check_and_create_group(problem_id: int, db: Session):
    """
    Helper function: Check if enough users have accepted and create/update group.
    
    Business Rule: ONE active group per problem with minimum 2 members
    
    Returns: (group_created: bool, group: CollaborationGroup or None)
    
    Future Extensions:
    - Add configurable MIN_GROUP_SIZE per problem
    - Premium users can create instant groups
    - Generate firebase_room_id when group is created (Phase 3)
    """
    # Get all accepted requests for this problem
    accepted_requests = db.query(CollaborationRequest).filter(
        CollaborationRequest.problem_id == problem_id,
        CollaborationRequest.status == 'accepted'
    ).all()
    
    # Check if we have minimum members
    if len(accepted_requests) < MIN_GROUP_SIZE:
        return False, None
    
    # Check if group already exists for this problem (ONE group per problem rule)
    group = db.query(CollaborationGroup).filter(
        CollaborationGroup.problem_id == problem_id
    ).first()
    
    if group:
        # Group exists, add any new members
        existing_member_ids = {member.id for member in group.members}
        new_members = [req.user for req in accepted_requests if req.user_id not in existing_member_ids]
        
        for member in new_members:
            group.members.append(member)
        
        group.is_active = True  # Ensure it's active
        db.commit()
        db.refresh(group)
        return False, group  # Group already existed
    else:
        # Create new group
        group = CollaborationGroup(
            problem_id=problem_id,
            is_active=True
        )
        
        # Add all accepted users as members
        for req in accepted_requests:
            group.members.append(req.user)
        
        db.add(group)
        db.commit()
        db.refresh(group)
        return True, group  # New group created


@app.post("/collaborate/request", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def request_collaboration(
    request: CollaborationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request to collaborate on a problem.
    
    Business Rules:
    - User must be authenticated
    - User must have marked interest in the problem first
    - One request per user per problem (enforced by unique constraint)
    - Creates request with status='pending'
    
    Future Extensions:
    - Add optional 'message' field for user's pitch/introduction
    - Add expiry date (auto-reject after 7 days)
    - Premium users get priority/instant acceptance
    - Send notification to other interested users
    """
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == request.problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if user has marked interest
    if current_user not in problem.interested_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must mark interest in this problem before requesting collaboration"
        )
    
    # Check for existing request (will also be caught by unique constraint)
    existing = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a collaboration request for this problem (status: {existing.status})"
        )
    
    # Create collaboration request
    collab_request = CollaborationRequest(
        user_id=current_user.id,
        problem_id=request.problem_id,
        status='pending'
    )
    
    db.add(collab_request)
    db.commit()
    db.refresh(collab_request)
    
    return {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "message": "Collaboration request created successfully. Accept it to join the collaboration!",
        "created_at": collab_request.created_at
    }


@app.post("/collaborate/accept", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def accept_collaboration(
    request: CollaborationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept your collaboration request for a problem.
    
    Business Rules:
    - Finds user's pending/accepted request
    - Updates status to 'accepted'
    - If ≥2 users accepted, auto-creates/updates collaboration group
    - ONE group per problem (adds user to existing group if it exists)
    
    Future Extensions:
    - Generate Firebase room ID when group is created
    - Send notifications to all group members
    - Premium users can invite specific collaborators
    - Add group chat initialization
    """
    # Find user's request for this problem
    collab_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if not collab_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a collaboration request for this problem. Create one first."
        )
    
    # Update status to accepted
    collab_request.status = 'accepted'
    db.commit()
    
    # Check if we should create/update a group
    group_created, group = check_and_create_group(request.problem_id, db)
    
    response_data = {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "created_at": collab_request.created_at,
        "group_created": group_created
    }
    
    if group:
        response_data["group_id"] = group.id
        response_data["total_members"] = len(group.members)
        response_data["collaborators"] = [member.username for member in group.members]
        response_data["message"] = f"Collaboration accepted! You're now in a group with {len(group.members)} members."
    else:
        response_data["message"] = "Collaboration accepted! Waiting for more users to join..."
    
    return response_data


@app.post("/collaborate/reject", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def reject_collaboration(
    request: CollaborationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject/withdraw your collaboration request.
    
    Business Rules:
    - Updates request status to 'rejected'
    - If user was in a group, removes them
    - If group drops below 2 members, deactivates the group
    - Allows withdrawal even after accepting (accepted → rejected)
    
    Future Extensions:
    - Add 'reason' field for rejection
    - Notify other group members when someone leaves
    - Archive group chat history before deactivation
    """
    # Find user's request
    collab_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if not collab_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a collaboration request for this problem"
        )
    
    # Update status to rejected
    old_status = collab_request.status
    collab_request.status = 'rejected'
    
    # If user was accepted and possibly in a group, handle group membership
    if old_status == 'accepted':
        group = db.query(CollaborationGroup).filter(
            CollaborationGroup.problem_id == request.problem_id
        ).first()
        
        if group and current_user in group.members:
            # Remove user from group
            group.members.remove(current_user)
            
            # If group now has less than minimum members, deactivate it
            if len(group.members) < MIN_GROUP_SIZE:
                group.is_active = False
    
    db.commit()
    
    return {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "message": "Collaboration request rejected/withdrawn successfully",
        "created_at": collab_request.created_at
    }


@app.get("/collaborate/{problem_id}", response_model=CollaborationStatusResponse, tags=["Collaboration"])
def get_collaboration_status(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get collaboration status for a problem.
    
    Returns:
    - Your request status (if any)
    - Total/pending/accepted request counts
    - Active group information
    - Whether you can request collaboration
    
    Future Extensions:
    - Show pending requests from other users (for group admins)
    - Add 'recommended collaborators' based on skills
    - Show group activity metrics
    - Link to Firebase chat room if group exists
    """
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Get user's request if exists
    user_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == problem_id
    ).first()
    
    # Get all requests for this problem
    all_requests = db.query(CollaborationRequest).filter(
        CollaborationRequest.problem_id == problem_id
    ).all()
    
    total_requests = len(all_requests)
    pending_requests = len([r for r in all_requests if r.status == 'pending'])
    accepted_requests = len([r for r in all_requests if r.status == 'accepted'])
    
    # Get active group if exists
    group = db.query(CollaborationGroup).filter(
        CollaborationGroup.problem_id == problem_id,
        CollaborationGroup.is_active == True
    ).first()
    
    # Determine if user can request collaboration
    can_request = current_user in problem.interested_users and user_request is None
    reason = None
    
    if not can_request:
        if current_user not in problem.interested_users:
            reason = "You must mark interest in this problem first"
        elif user_request:
            reason = f"You already have a request (status: {user_request.status})"
    
    # Build response
    response = {
        "problem_id": problem.ps_id,
        "problem_title": problem.title,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "accepted_requests": accepted_requests,
        "can_request": can_request,
        "reason": reason
    }
    
    if user_request:
        response["your_request"] = {
            "request_id": user_request.id,
            "status": user_request.status,
            "created_at": user_request.created_at
        }
    
    if group:
        response["active_group"] = {
            "group_id": group.id,
            "member_count": len(group.members),
            "members": [member.username for member in group.members],
            "created_at": group.created_at,
            "is_active": group.is_active
        }
    
    return response





# ============ Debug Endpoints ============

@app.get("/db-info", tags=["Debug"])
def get_database_info(db: Session = Depends(get_db)):
    """
    Debug endpoint: Show which database is actually being used.
    
    Returns database URL and type (SQLite vs PostgreSQL).
    Useful for verifying production database connection.
    """
    from sqlalchemy import inspect
    
    # Get database URL (hide password)
    db_url_str = str(engine.url)
    if "@" in db_url_str:
        # Format: postgresql://user:pass@host:port/db
        db_display = db_url_str.split("://")[0] + "://" + db_url_str.split("@")[-1]
    else:
        db_display = db_url_str
    
    # Determine database type
    if "postgresql" in db_url_str:
        db_type = "PostgreSQL"
        status = "🎉 Production Ready!"
    elif "sqlite" in db_url_str:
        db_type = "SQLite"
        status = "⚠️ Development Mode"
    else:
        db_type = "Unknown"
        status = "❓ Unknown Database"
    
    # Count tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    return {
        "database_type": db_type,
        "database_url": db_display,
        "total_tables": len(tables),
        "tables": sorted(tables),
        "status": status
    }


# ============ Health Check ============


@app.get("/", tags=["Health"])
def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "message": "SolveStack API is running",
        "version": "1.0.0"
    }


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
