from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Table, Boolean, UniqueConstraint, Index, Float, SmallInteger, Date
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

Base = declarative_base()

# Association table for many-to-many relationship between users and problems
problem_interests = Table('problem_interests', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('problem_id', Integer, ForeignKey('problems.ps_id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    """User model for authentication and collaboration"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Relationships
    interested_problems = relationship(
        'Problem', 
        secondary=problem_interests, 
        back_populates='interested_users'
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Problem(Base):
    """Problem model - scraped from Reddit, GitHub, etc."""
    __tablename__ = 'problems'
    
    ps_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    source = Column(String(100))  # 'reddit/subreddit', 'github/repo', etc.
    source_id = Column(String(100))  # ID from source (e.g., issue #, post ID)
    date = Column(Date)  # Date from source
    suggested_tech = Column(String(500))  # Comma-separated tech tags
    author_name = Column(String(100))
    author_id = Column(String(100))
    reference_link = Column(String(500), unique=True, nullable=False, index=True)
    tags = Column(JSON)  # Array of tags from source (legacy/deprecated)
    
    # Raw Fields (Preserving original data)
    raw_title = Column(Text)
    raw_description = Column(Text)
    raw_tags = Column(JSON)
    
    # Processed/Cleaned Fields
    cleaned_title = Column(Text)
    cleaned_description = Column(Text)
    normalized_title = Column(Text)
    title_hash = Column(String(64), index=True) # SHA-256 hash for deduplication
    
    # Scoring and Metadata Fields
    difficulty_score = Column(Float, default=0.0)
    difficulty_level = Column(SmallInteger, default=0) # 0: Unknown, 1: Easy, 2: Medium, 3: Hard
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    
    # Metrics and Features
    text_length = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    has_code_block = Column(Boolean, default=False)
    num_code_blocks = Column(Integer, default=0)
    
    # Audit/Version Info
    scraped_at = Column(DateTime, default=datetime.utcnow)
    cleaned_at = Column(DateTime, default=datetime.utcnow)
    clean_version = Column(String(20), default="1.0.0")
    
    # Engineering Impact Scoring (EIS) - Phase 1
    technical_depth_score = Column(Float, default=0.0)
    industry_impact_score = Column(Float, default=0.0)
    cognitive_complexity_score = Column(Float, default=0.0)
    signal_quality_score = Column(Float, default=0.0)
    engineering_impact_score = Column(Float, default=0.0, index=True) # Normalized 0-100
    scoring_version = Column(String(20), default="1.0.0")
    
    # Semantic Search Support (pgvector)
    # Default to 384 dimensions (e.g., for all-MiniLM-L6-v2)
    if Vector is not None:
        embedding = Column(Vector(384), nullable=True)
    else:
        # Fallback for SQLite/Dev where pgvector isn't installed
        embedding = Column(JSON, nullable=True) # Store as array/list of floats
        
    # Full-Text Search Support (PostgreSQL)
    search_vector = Column(TSVECTOR)
    
    # Relationships
    interested_users = relationship(
        'User', 
        secondary=problem_interests, 
        back_populates='interested_problems'
    )
    collaboration_groups = relationship('CollaborationGroup', back_populates='problem')
    
    # Composite index for de-duplication
    __table_args__ = (
        Index('idx_source_source_id', 'source', 'source_id'),
    )
    
    def __repr__(self):
        return f"<Problem(ps_id={self.ps_id}, title='{self.title[:50]}...', source='{self.source}')>"


# Association table for many-to-many relationship between groups and users
group_members = Table('group_members', Base.metadata,
    Column('group_id', Integer, ForeignKey('collaboration_groups.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class CollaborationRequest(Base):
    """
    Tracks collaboration requests from users.
    
    Business Rules:
    - User must have marked interest in the problem before requesting
    - One request per user per problem (unique constraint)
    - Status transitions: pending → accepted/rejected
    - Users can withdraw (accepted → rejected)
    
    Future Extensions:
    - Add 'message' field for request notes/pitch
    - Add 'expiry_date' for time-limited requests (auto-reject after 7 days)
    - Add 'priority' field for premium users (Stripe integration)
    - Link to notification system for real-time alerts
    """
    __tablename__ = 'collaboration_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.ps_id'), nullable=False)
    status = Column(String(20), default='pending', nullable=False)  # pending/accepted/rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='collaboration_requests')
    problem = relationship('Problem', backref='collaboration_requests')
    
    # Constraints and Indexes
    __table_args__ = (
        # Prevent duplicate requests from same user for same problem
        UniqueConstraint('user_id', 'problem_id', name='unique_user_problem_request'),
        # Fast lookup of requests by problem and status (for group formation)
        Index('idx_problem_status', 'problem_id', 'status'),
    )
    
    def __repr__(self):
        return f"<CollaborationRequest(id={self.id}, user_id={self.user_id}, problem_id={self.problem_id}, status='{self.status}')>"


class CollaborationGroup(Base):
    """
    Represents active collaboration groups for a problem.
    
    Business Rules:
    - ONE group per problem (enforced at application level)
    - Minimum 2 members to create/maintain a group
    - Auto-created when ≥2 users have accepted status
    - If members drop below 2, group becomes inactive
    
    Future Extensions:
    - firebase_room_id: Link to Firebase Realtime Database chat room (Phase 3)
    - is_premium: Flag for Stripe premium groups with extra features
    - max_members: Configurable group size limits
    - group_name: User-defined group names
    - tags: Skill tags for smart matching
    """
    __tablename__ = 'collaboration_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('problems.ps_id'), nullable=False, unique=True)  # ONE group per problem
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Firebase room ID (nullable for now, will be set in Phase 3)
    # Format: "room_{problem_id}_{uuid}" for uniqueness
    firebase_room_id = Column(String(100), unique=True, nullable=True)
    
    # Relationships
    problem = relationship('Problem', back_populates='collaboration_groups')
    
    # Many-to-many with users (group members)
    members = relationship(
        'User',
        secondary=group_members,
        backref='joined_collaboration_groups'
    )
    
    def __repr__(self):
        return f"<CollaborationGroup(id={self.id}, problem_id={self.problem_id}, members={len(self.members)}, active={self.is_active})>"


class SearchLog(Base):
    """
    Tracks search queries for intent-aware tuning.
    """
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    results_returned = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<SearchLog(id={self.id}, query='{self.query[:30]}...', results={self.results_returned})>"
