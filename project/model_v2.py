# models_v2.py - Database models (with direct district association)

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table, desc, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# Poll-ZipCode association table
poll_zipcodes = Table(
    'poll_zipcodes',
    Base.metadata,
    Column('poll_id', Integer, ForeignKey('polls.id', ondelete='CASCADE'), primary_key=True),
    Column('zipcode_id', Integer, ForeignKey('zipcodes.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_poll_zip', 'poll_id', 'zipcode_id')
)

# Poll-District association table (new)
poll_districts = Table(
    'poll_districts',
    Base.metadata,
    Column('poll_id', Integer, ForeignKey('polls.id', ondelete='CASCADE'), primary_key=True),
    Column('district_id', Integer, ForeignKey('schools.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_poll_districts_poll', 'poll_id'),
    Index('idx_poll_districts_district', 'district_id')
)


class Poll(Base):
    """Poll table"""
    __tablename__ = 'polls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    description = Column(Text)
    
    poll_type = Column(String(50), nullable=False, default='single_choice')
    
    min_choices = Column(Integer, default=1)
    max_choices = Column(Integer)
    
    rating_min = Column(Integer, default=1)
    rating_max = Column(Integer, default=5)
    rating_labels = Column(Text)
    
    options = Column(Text, nullable=False)
    
    cities = Column(Text)
    states = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)
    
    # Relationships
    zipcodes = relationship('ZipCode', secondary=poll_zipcodes, back_populates='polls', lazy='joined')
    votes = relationship('Vote', back_populates='poll', cascade='all, delete-orphan')
    districts = relationship('School', secondary=poll_districts, back_populates='polls', lazy='joined')
    
    def get_options(self):
        return json.loads(self.options) if self.options else []
    
    def set_options(self, options_list):
        self.options = json.dumps(options_list, ensure_ascii=False)
    
    def get_cities(self):
        return json.loads(self.cities) if self.cities else []
    
    def set_cities(self, cities_list):
        self.cities = json.dumps(cities_list, ensure_ascii=False)
    
    def get_states(self):
        return json.loads(self.states) if self.states else []
    
    def set_states(self, states_list):
        self.states = json.dumps(states_list, ensure_ascii=False)
    
    def get_rating_labels(self):
        return json.loads(self.rating_labels) if self.rating_labels else {}
    
    def set_rating_labels(self, labels_dict):
        self.rating_labels = json.dumps(labels_dict, ensure_ascii=False)
    
    def __repr__(self):
        return f"<Poll(id={self.id}, type={self.poll_type}, title='{self.title}')>"


class ZipCode(Base):
    """ZipCode table"""
    __tablename__ = 'zipcodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zip_code = Column(String(10), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(2), nullable=False, index=True)
    county = Column(String(100))
    
    __table_args__ = (
        Index('idx_zip_city_state', 'zip_code', 'city', 'state'),
        Index('idx_city_state', 'city', 'state'),
    )
    
    polls = relationship('Poll', secondary=poll_zipcodes, back_populates='zipcodes')
    
    def __repr__(self):
        return f"<ZipCode(zip={self.zip_code}, city='{self.city}', state='{self.state}')>"


class Vote(Base):
    """Vote record table"""
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey('polls.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, default=0)
    
    choice = Column(Integer)
    choices = Column(Text)
    rating = Column(Integer)
    ranking = Column(Text)
    
    voted_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    poll = relationship('Poll', back_populates='votes')
    
    def get_choices(self):
        return json.loads(self.choices) if self.choices else []
    
    def set_choices(self, choices_list):
        self.choices = json.dumps(choices_list)
    
    def get_ranking(self):
        return json.loads(self.ranking) if self.ranking else []
    
    def set_ranking(self, ranking_list):
        self.ranking = json.dumps(ranking_list)
    
    def __repr__(self):
        return f"<Vote(poll_id={self.poll_id}, user_id={self.user_id})>"


class User(Base):
    """User table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zip_code = Column(String(10))
    age = Column(Integer)
    gender = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, zip={self.zip_code})>"


class Admin(Base):
    """Admin table"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}')>"


class School(Base):
    """School/district data table"""
    __tablename__ = 'schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cds_code = Column(String(20), unique=True, nullable=False, index=True)
    record_type = Column(String(20), nullable=False)
    county = Column(String(100), nullable=False, index=True)
    district = Column(String(200), nullable=False, index=True)
    school = Column(String(200))
    status = Column(String(50))
    entity_type = Column(String(100))
    city = Column(String(100), index=True)
    zip_code = Column(String(10), index=True)
    
    __table_args__ = (
        Index('idx_district_city', 'district', 'city'),
        Index('idx_county_district', 'county', 'district'),
    )
    
    polls = relationship('Poll', secondary=poll_districts, back_populates='districts')
    
    def __repr__(self):
        return f"<School(cds={self.cds_code}, district='{self.district}')>"


# Database initialization
def init_db(db_path='sqlite:///polling_v2.db'):
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    print(f"Database created at: {db_path}")
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


# Query functions
def get_polls_by_zipcode(db, zip_code):
    zipcode_obj = db.query(ZipCode).filter_by(zip_code=zip_code).first()
    
    if not zipcode_obj:
        return []
    
    polls = db.query(Poll).join(
        poll_zipcodes
    ).filter(
        poll_zipcodes.c.zipcode_id == zipcode_obj.id,
        Poll.is_active == 1
    ).order_by(desc(Poll.created_at)).all()
    
    return polls


def get_polls_by_city(db, city, state=None):
    query = db.query(ZipCode).filter(ZipCode.city.ilike(city))
    
    if state:
        query = query.filter_by(state=state.upper())
    
    zipcodes = query.all()
    
    if not zipcodes:
        return []
    
    zipcode_ids = [zc.id for zc in zipcodes]
    
    polls = db.query(Poll).join(
        poll_zipcodes
    ).filter(
        poll_zipcodes.c.zipcode_id.in_(zipcode_ids),
        Poll.is_active == 1
    ).order_by(desc(Poll.created_at)).distinct().all()
    
    return polls


def get_polls_by_district(db, district_name):
    """Get polls by district name (direct association)"""
    districts = db.query(School).filter(
        School.district.ilike(f'%{district_name}%'),
        School.record_type == 'District'
    ).all()
    
    if not districts:
        return []
    
    district_ids = [d.id for d in districts]
    
    polls = db.query(Poll).join(
        poll_districts
    ).filter(
        poll_districts.c.district_id.in_(district_ids),
        Poll.is_active == 1
    ).order_by(desc(Poll.created_at)).distinct().all()
    
    return polls


def get_poll_by_id(db, poll_id):
    return db.query(Poll).filter_by(id=poll_id).first()


def get_all_polls(db):
    return db.query(Poll).order_by(desc(Poll.created_at)).all()


# Vote functions
def add_vote_single_choice(db, poll_id, choice, user_id=0):
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        choice=choice
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_multiple_choice(db, poll_id, choices, user_id=0):
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_choices(choices)
    db.add(vote)
    db.commit()
    return vote


def add_vote_rating(db, poll_id, rating, user_id=0):
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        rating=rating
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_ranked(db, poll_id, ranking, user_id=0):
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_ranking(ranking)
    db.add(vote)
    db.commit()
    return vote


def get_poll_results(db, poll_id):
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        return None
    
    votes = db.query(Vote).filter_by(poll_id=poll_id).all()
    total_votes = len(votes)
    
    results = {
        'poll': poll,
        'total_votes': total_votes,
        'results': {}
    }
    
    if poll.poll_type == 'single_choice':
        options = poll.get_options()
        for i, option in enumerate(options):
            count = sum(1 for v in votes if v.choice == i)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            results['results'][option] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
    
    elif poll.poll_type == 'multiple_choice':
        options = poll.get_options()
        for i, option in enumerate(options):
            count = sum(1 for v in votes if i in v.get_choices())
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            results['results'][option] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
    
    elif poll.poll_type == 'rating_scale':
        if total_votes > 0:
            ratings = [v.rating for v in votes if v.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            rating_counts = {}
            for r in range(poll.rating_min, poll.rating_max + 1):
                count = sum(1 for rating in ratings if rating == r)
                rating_counts[str(r)] = count
            
            results['results'] = {
                'average': round(avg_rating, 2),
                'ratings': rating_counts,
                'min': poll.rating_min,
                'max': poll.rating_max
            }
    
    elif poll.poll_type == 'ranked_choice':
        options = poll.get_options()
        rankings = [v.get_ranking() for v in votes if v.ranking]
        
        option_scores = {}
        for i, option in enumerate(options):
            positions = []
            for ranking in rankings:
                if i in ranking:
                    positions.append(ranking.index(i) + 1)
            
            avg_position = sum(positions) / len(positions) if positions else 0
            option_scores[option] = {
                'average_rank': round(avg_position, 2),
                'times_ranked': len(positions)
            }
        
        results['results'] = option_scores
    
    return results


# Zip code queries
def get_zipcodes_by_city(db, city, state=None):
    query = db.query(ZipCode).filter(ZipCode.city.ilike(city))
    
    if state:
        query = query.filter_by(state=state.upper())
    
    return query.all()


def search_by_city_or_zip(db, query):
    query = query.strip()
    
    if query.isdigit() and len(query) == 5:
        results = db.query(ZipCode).filter_by(zip_code=query).all()
        return results
    
    if ',' in query:
        parts = query.split(',')
        city = parts[0].strip()
        state = parts[1].strip().upper() if len(parts) > 1 else None
        
        if state and len(state) == 2:
            results = db.query(ZipCode).filter(
                ZipCode.city.ilike(city),
                ZipCode.state == state
            ).all()
        else:
            results = db.query(ZipCode).filter(
                ZipCode.city.ilike(f'%{city}%')
            ).all()
    else:
        results = db.query(ZipCode).filter(
            ZipCode.city.ilike(f'%{query}%')
        ).all()
    
    return results


# District queries
def search_schools(db, query):
    """Search districts/schools"""
    query = query.strip()
    
    if query.isdigit() and len(query) == 5:
        return db.query(School).filter_by(zip_code=query).all()
    
    results = db.query(School).filter(
        (School.district.ilike(f'%{query}%')) |
        (School.city.ilike(f'%{query}%')) |
        (School.county.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return results


def get_districts_by_city(db, city):
    """Get districts by city"""
    return db.query(School).filter(
        School.city.ilike(city),
        School.record_type == 'District'
    ).distinct().all()


def get_districts_by_zipcode(db, zip_code):
    """Get districts by zip code"""
    return db.query(School).filter(
        School.zip_code == zip_code,
        School.record_type == 'District'
    ).all()


def get_zipcodes_by_district(db, district_name):
    """Get all zip codes by district name"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    zipcodes = list(set([s.zip_code for s in schools if s.zip_code]))
    return zipcodes