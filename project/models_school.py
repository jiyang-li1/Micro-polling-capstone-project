# models_school.py - 学区投票系统数据模型（纯学区版）

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Table, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# ============================================
# 关联表：投票 ↔ 学区
# ============================================

poll_schools = Table('poll_schools', Base.metadata,
    Column('poll_id', Integer, ForeignKey('polls.id', ondelete='CASCADE')),
    Column('school_id', Integer, ForeignKey('schools.id', ondelete='CASCADE'))
)

# ============================================
# 学区/学校表
# ============================================

class School(Base):
    """学区/学校数据表"""
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
    
    # 关系
    polls = relationship('Poll', secondary=poll_schools, back_populates='schools')
    
    __table_args__ = (
        Index('idx_district_city', 'district', 'city'),
        Index('idx_county_district', 'county', 'district'),
    )
    
    def __repr__(self):
        return f"<School(district='{self.district}', city='{self.city}')>"


# ============================================
# 投票表
# ============================================

class Poll(Base):
    """投票表"""
    __tablename__ = 'polls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    description = Column(Text)
    
    # 投票类型
    poll_type = Column(String(50), nullable=False, default='single_choice')
    # single_choice, multiple_choice, rating_scale, ranked_choice
    
    # 选项（JSON 存储）
    options = Column(Text)  # JSON array
    
    # 多选配置
    min_choices = Column(Integer, default=1)
    max_choices = Column(Integer)  # NULL = 无限制
    
    # 量表配置
    rating_min = Column(Integer, default=1)
    rating_max = Column(Integer, default=5)
    rating_labels = Column(Text)  # JSON object: {1: "Very Bad", 5: "Very Good"}
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    
    # 关系
    schools = relationship('School', secondary=poll_schools, back_populates='polls', lazy='joined')
    votes = relationship('Vote', back_populates='poll', cascade='all, delete-orphan')
    
    def get_options(self):
        """获取选项列表"""
        if self.options:
            return json.loads(self.options)
        return []
    
    def set_options(self, options_list):
        """设置选项列表"""
        self.options = json.dumps(options_list)
    
    def get_rating_labels(self):
        """获取量表标签"""
        if self.rating_labels:
            return json.loads(self.rating_labels)
        return {}
    
    def set_rating_labels(self, labels_dict):
        """设置量表标签"""
        self.rating_labels = json.dumps(labels_dict)
    
    def __repr__(self):
        return f"<Poll(id={self.id}, title='{self.title}')>"


# ============================================
# 投票记录表
# ============================================

class Vote(Base):
    """投票记录表"""
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey('polls.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, default=0)  # 0 = 匿名
    
    # 不同投票类型的答案存储
    choice = Column(Integer)  # 单选
    choices = Column(Text)  # 多选（JSON array）
    rating = Column(Integer)  # 量表
    ranking = Column(Text)  # 排序（JSON array）
    
    voted_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    poll = relationship('Poll', back_populates='votes')
    
    def get_choices(self):
        """获取多选答案"""
        if self.choices:
            return json.loads(self.choices)
        return []
    
    def set_choices(self, choices_list):
        """设置多选答案"""
        self.choices = json.dumps(choices_list)
    
    def get_ranking(self):
        """获取排序答案"""
        if self.ranking:
            return json.loads(self.ranking)
        return []
    
    def set_ranking(self, ranking_list):
        """设置排序答案"""
        self.ranking = json.dumps(ranking_list)
    
    def __repr__(self):
        return f"<Vote(id={self.id}, poll_id={self.poll_id})>"


# ============================================
# 管理员表
# ============================================

class Admin(Base):
    """管理员表"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Admin(username='{self.username}')>"


# ============================================
# 数据库初始化
# ============================================

def init_db(db_url='sqlite:///polling_school.db'):
    """初始化数据库"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    print(f"Database created at: {db_url}")
    return engine


def get_session(engine):
    """获取数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================
# 查询函数
# ============================================

def search_schools(db, query):
    """
    搜索学区/学校
    支持：学区名、城市名、邮编、县名
    """
    query = query.strip()
    
    # 如果是5位数字，当作邮编
    if query.isdigit() and len(query) == 5:
        return db.query(School).filter_by(zip_code=query).all()
    
    # 否则搜索学区名、城市名、县名
    results = db.query(School).filter(
        (School.district.ilike(f'%{query}%')) |
        (School.city.ilike(f'%{query}%')) |
        (School.county.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return results


def get_districts(db):
    """获取所有学区（去重）"""
    return db.query(
        School.district,
        School.county
    ).filter(
        School.record_type == 'District'
    ).distinct().all()


def get_schools_by_district(db, district_name):
    """根据学区名获取所有学校/记录"""
    return db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()


def get_zipcodes_by_district(db, district_name):
    """根据学区名获取所有邮编"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    zipcodes = list(set([s.zip_code for s in schools if s.zip_code]))
    return sorted(zipcodes)


def get_cities_by_district(db, district_name):
    """根据学区名获取所有城市"""
    schools = db.query(School).filter(
        School.district.ilike(f'%{district_name}%')
    ).all()
    
    cities = list(set([s.city for s in schools if s.city]))
    return sorted(cities)


def get_poll_by_id(db, poll_id):
    """根据 ID 获取投票（预加载学区）"""
    return db.query(Poll).filter_by(id=poll_id).first()


def get_polls_by_school_id(db, school_id):
    """根据学校 ID 获取投票"""
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
    """根据学区名获取投票"""
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
    """根据邮编获取投票"""
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
    """根据城市获取投票"""
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
    """添加单选投票"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        choice=choice
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_multiple_choice(db, poll_id, choices, user_id=0):
    """添加多选投票"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_choices(choices)
    db.add(vote)
    db.commit()
    return vote


def add_vote_rating(db, poll_id, rating, user_id=0):
    """添加量表投票"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id,
        rating=rating
    )
    db.add(vote)
    db.commit()
    return vote


def add_vote_ranked(db, poll_id, ranking, user_id=0):
    """添加排序投票"""
    vote = Vote(
        poll_id=poll_id,
        user_id=user_id
    )
    vote.set_ranking(ranking)
    db.add(vote)
    db.commit()
    return vote


def get_poll_results(db, poll_id):
    """获取投票结果（支持所有类型）"""
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
    """获取所有投票"""
    return db.query(Poll).order_by(Poll.created_at.desc()).all()