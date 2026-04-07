# models_school.py - School district voting system data model (pure district version)

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Table, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# ============================================
# Association table: Poll ↔ School
# ============================================

poll_schools = Table('poll_schools', Base.metadata,
    Column('poll_id', Integer, ForeignKey('polls.id', ondelete='CASCADE')),
    Column('school_id', Integer, ForeignKey('schools.id', ondelete='CASCADE'))
)

# ============================================
# School/District table
# ============================================

class School(Base):
    """School/district data table"""
    __tablename__ = 'schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cds_code = Column(String(20), unique=True, nullable=False, index=True)
    record_type = Column(String(20), nullable=False)  # District or School
    county = Column(String(100), nullable=False, index=True)
    district = Column(String(200), nullable=False, index=True)
    school = Column(String(200))
    status = Column(String(50))
    entity_type = Column(String(100))
    city = Column(String(100), index=True)
    zip_code = Column(String(10), index=True)
    
    # Relationship
    polls = relationship('Poll', secondary=poll_schools, back_populates='schools')
    
    __table_args__ = (
        Index('idx_district_city', 'district', 'city'),
        Index('idx_county_district', 'county', 'district'),
    )
    
    def __repr__(self):
        return f"<School(district='{self.district}', city='{self.city}')>"


# ============================================
# Poll table
# ============================================

class Poll(Base):
    """Poll table"""
    __tablename__ = 'polls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    description = Column(Text)
    
    # Poll type
    poll_type = Column(String(50), nullable=False, default='single_choice')
    # single_choice, multiple_choice, rating_scale, ranked_choice
    
    # Options (stored as JSON)
    options = Column(Text)  # JSON array
    
    # Multiple choice configuration
    min_choices = Column(Integer, default=1)
    max_choices = Column(Integer)  # NULL = unlimited
    
    # Rating scale configuration
    rating_min = Column(Integer, default=1)
    rating_max = Column(Integer, default=5)
    rating_labels = Column(Text)  # JSON object: {1: "Very Bad", 5: "Very Good"}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    
    # Relationships
    schools = relationship('School', secondary=poll_schools, back_populates='polls', lazy='joined')
    votes = relationship('Vote', back_populates='poll', cascade='all, delete-orphan')
    
    def get_options(self):
        """Get options list"""
        if self.options:
            return json.loads(self.options)
        return []
    
    def set_options(self, options_list):
        """Set options list"""
        self.options = json.dumps(options_list)
    
    def get_rating_labels(self):
        """Get rating scale labels"""
        if self.rating_labels:
            return json.loads(self.rating_labels)
        return {}
    
    def set_rating_labels(self, labels_dict):
        """Set rating scale labels"""
        self.rating_labels = json.dumps(labels_dict)
    
    def __repr__(self):
        return f"<Poll(id={self.id}, title='{self.title}')>"


# ============================================
# Vote record table
# ============================================

class Vote(Base):
    """Vote record table"""
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey('polls.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, default=0)  # 0 = anonymous
    
    # Answer storage for different poll types
    choice = Column(Integer)  # single choice
    choices = Column(Text)  # multiple choice (JSON array)
    rating = Column(Integer)  # rating scale
    ranking = Column(Text)  # ranked choice (JSON array)
    
    voted_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    poll = relationship('Poll', back_populates='votes')
    
    def get_choices(self):
        """Get multiple choice answers"""
        if self.choices:
            return json.loads(self.choices)
        return []
    
    def set_choices(self, choices_list):
        """Set multiple choice answers"""
        self.choices = json.dumps(choices_list)
    
    def get_ranking(self):
        """Get ranked choice answers"""
        if self.ranking:
            return json.loads(self.ranking)
        return []
    
    def set_ranking(self, ranking_list):
        """Set ranked choice answers"""
        self.ranking = json.dumps(ranking_list)
    
    def __repr__(self):
        return f"<Vote(id={self.id}, poll_id={self.poll_id})>"


# ============================================
# Admin table
# ============================================

class Admin(Base):
    """Admin table"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Admin(username='{self.username}')>"


# ============================================
# Database initialization
# ============================================

def init_db(db_url='sqlite:///polling_school.db'):
    """Initialize database"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    print(f"Database created at: {db_url}")
    return engine


def get_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================
# Query functions
# ============================================

def search_schools(db, query):
    """
    Search districts/schools
    Supports: district name, city name, zip code, county name
    """
    query = query.strip()
    
    # If it's a 5-digit number, treat as zip code
    if query.isdigit() and len(query) == 5:
        return db.query(School).filter_by(zip_code=query).all()
    
    # Otherwise search by district name, city name, county name
    results = db.query(School).filter(
        (School.district.ilike(f'%{query}%')) |
        (School.city.ilike(f'%{query}%')) |
        (School.county.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return results


def get_districts(db):
    """Get all districts (deduplicated)"""
    return db.query(
        School.district,
        School.county
    ).filter(
        School.record_type == 'District'
    ).distinct().all()


def get_schools_by_district(db, district_name):
    """Get all schools/records by district name"""
    return db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()


def get_zipcodes_by_district(db, district_name):
    """Get all zip codes by district name"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    zipcodes = list(set([s.zip_code for s in schools if s.zip_code]))
    return sorted(zipcodes)


def get_cities_by_district(db, district_name):
    """Get all cities by district name"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    cities = list(set([s.city for s in schools if s.city]))
    return sorted(cities)


def get_poll_by_id(db, poll_id):
    """Get poll by ID (with preloaded schools)"""
    return db.query(Poll).filter_by(id=poll_id).first()


def get_polls_by_school_id(db, school_id):
    """Get polls by school ID"""
    school = db.query(School).filter_by(id=school_id).first()
    if not school:
        return []
    
    return db.query(Poll).join(
        poll_schools
    ).filter(
        poll_schools.c.school_id == school_id,
        Poll.is_active == 1
    ).all()


def get_polls_by_district(db, district_name):
    """Get polls by district name"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    if not schools:
        return []
    
    school_ids = [s.id for s in schools]
    
    return db.query(Poll).join(
        poll_schools
    ).filter(
        poll_schools.c.school_id.in_(school_ids),
        Poll.is_active == 1
    ).distinct().all()


def get_polls_by_zipcode(db, zip_code):
    """Get polls by zip code"""
    schools = db.query(School).filter_by(zip_code=zip_code).all()
    
    if not schools:
        return []
    
    school_ids = [s.id for s in schools]
    
    return db.query(Poll).join(
        poll_schools
    ).filter(
        poll_schools.c.school_id.in_(school_ids),
        Poll.is_active == 1
    ).distinct().all()


def get_polls_by_city(db, city):
    """Get polls by city"""
    schools = db.query(School).filter(
        School.city.ilike(city)
    ).all()
    
    if not schools:
        return []
    
    school_ids = [s.id for s in schools]
    
    return db.query(Poll).join(
        poll_schools
    ).filter(
        poll_schools.c.school_id.in_(school_ids),
        Poll.is_active == 1
    ).distinct().all()


def add_vote_single_choice(db, poll_id, choice, user_id=0):
    """Add single choice vote"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        choice=choice
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_multiple_choice(db, poll_id, choices, user_id=0):
    """Add multiple choice vote"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_choices(choices)
    db.add(vote)
    db.commit()
    return vote


def add_vote_rating(db, poll_id, rating, user_id=0):
    """Add rating scale vote"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        rating=rating
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_ranked(db, poll_id, ranking, user_id=0):
    """Add ranked choice vote"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_ranking(ranking)
    db.add(vote)
    db.commit()
    return vote


def get_poll_results(db, poll_id):
    """Get poll results (supports all types)"""
    poll = get_poll_by_id(db, poll_id)
    if not poll:
        return None
    
    votes = db.query(Vote).filter_by(poll_id=poll_id).all()
    total_votes = len(votes)
    
    results = {}
    
    if poll.poll_type == 'single_choice':
        options = poll.get_options()
        counts = {}
        
        for vote in votes:
            choice = vote.choice
            if choice is not None and choice < len(options):
                option_text = options[choice]
                counts[option_text] = counts.get(option_text, 0) + 1
        
        for option in options:
            count = counts.get(option, 0)
            percentage = round((count / total_votes * 100), 1) if total_votes > 0 else 0
            results[option] = {
                'count': count,
                'percentage': percentage
            }
    
    elif poll.poll_type == 'multiple_choice':
        options = poll.get_options()
        counts = {}
        
        for vote in votes:
            choices = vote.get_choices()
            for choice in choices:
                if choice < len(options):
                    option_text = options[choice]
                    counts[option_text] = counts.get(option_text, 0) + 1
        
        for option in options:
            count = counts.get(option, 0)
            percentage = round((count / total_votes * 100), 1) if total_votes > 0 else 0
            results[option] = {
                'count': count,
                'percentage': percentage
            }
    
    elif poll.poll_type == 'rating_scale':
        ratings = {}
        total_rating = 0
        
        for vote in votes:
            rating = vote.rating
            if rating:
                ratings[str(rating)] = ratings.get(str(rating), 0) + 1
                total_rating += rating
        
        average = round(total_rating / total_votes, 1) if total_votes > 0 else 0
        
        results = {
            'average': average,
            'ratings': ratings,
            'min': poll.rating_min,
            'max': poll.rating_max
        }
    
    elif poll.poll_type == 'ranked_choice':
        options = poll.get_options()
        rankings = {i: [] for i in range(len(options))}
        
        for vote in votes:
            ranking = vote.get_ranking()
            for position, option_index in enumerate(ranking):
                if option_index < len(options):
                    rankings[option_index].append(position + 1)
        
        for i, option in enumerate(options):
            positions = rankings[i]
            avg_rank = round(sum(positions) / len(positions), 1) if positions else len(options)
            results[option] = {
                'average_rank': avg_rank,
                'times_ranked': len(positions)
            }
    
    return {
        'poll': poll,
        'results': results,
        'total_votes': total_votes
    }


def get_all_polls(db):
    """Get all polls"""
    return db.query(Poll).order_by(Poll.created_at.desc()).all()