
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, desc
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Poll(Base):
    """
    - id: Poll id, primary key
    - zip_code: 5-digit zip code (string)
    - title: Poll title
    - question: poll question
    - options: poll options (JSON string)
    - created_at: creation timestamp
    - is_active: active status (1=active, 0=closed)
    """
    __tablename__ = 'polls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zip_code = Column(String(10), nullable=False, index=True)  
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON format: ["OptionA", "OptionB", "OptionC"]
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  
    is_active = Column(Integer, default=1)  

    votes = relationship('Vote', back_populates='poll', cascade='all, delete-orphan')
    
    def get_options(self):
        return json.loads(self.options)
    
    def set_options(self, options_list):
        self.options = json.dumps(options_list, ensure_ascii=False)
    
    def __repr__(self):
        return f"<Poll(id={self.id}, zip={self.zip_code}, title='{self.title}')>"



class Vote(Base):
    """
    - id: Primary key
    - poll_id: foreign key
    - choice: options index (0, 1, 2...)
    - voted_at: timestamp
    """
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey('polls.id'), nullable=False, index=True)
    choice = Column(Integer, nullable=False) 
    voted_at = Column(DateTime, default=datetime.utcnow)
    
    poll = relationship('Poll', back_populates='votes')
    
    def __repr__(self):
        return f"<Vote(poll_id={self.poll_id}, choice={self.choice})>"




def init_db(db_path='sqlite:///polling.db'):
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    print(f"DB created at: {db_path}")
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()




def get_latest_poll_by_zipcode(db, zip_code):
    poll = db.query(Poll).filter(
        Poll.zip_code == zip_code,
        Poll.is_active == 1
    ).order_by(desc(Poll.created_at)).first()
    
    return poll


def get_poll_by_id(db, poll_id):
    return db.query(Poll).filter_by(id=poll_id).first()


def get_all_polls(db):
    return db.query(Poll).order_by(desc(Poll.created_at)).all()


def add_vote(db, poll_id, choice):
    vote = Vote(
        poll_id=poll_id,
        choice=choice
    )
    db.add(vote)
    db.commit()
    return vote


def get_poll_results(db, poll_id):
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        return None

    votes = db.query(Vote).filter_by(poll_id=poll_id).all()
    
    options = poll.get_options()
    results = {}
    total_votes = len(votes)
    
    for i, option in enumerate(options):
        count = sum(1 for v in votes if v.choice == i)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        
        results[option] = {
            'count': count,
            'percentage': round(percentage, 1)
        }
    
    return {
        'poll': poll,
        'results': results,
        'total_votes': total_votes
    }




if __name__ == '__main__':

    engine = init_db('sqlite:///test_polling.db')
    db = get_session(engine)
    

    poll = Poll(
        zip_code="11111",
        title="Test Poll1",
        question="Test question1"
    )
    poll.set_options(["A", "B"])
    db.add(poll)
    db.commit()
    
    found_poll = get_latest_poll_by_zipcode(db, "11111")
    if found_poll:
        print(f"FOund poll : {found_poll.title}")
        print(f"Poll options: {found_poll.get_options()}")
    

    add_vote(db, poll.id, choice=0) 
    add_vote(db, poll.id, choice=0) 
    add_vote(db, poll.id, choice=1) 
    

    results = get_poll_results(db, poll.id)
    if results:
        print(f"Vote results for: {results['poll'].title}")
        print(f"Total votes: {results['total_votes']}")
        for option, data in results['results'].items():
            print(f"  {option}: {data['count']} votes ({data['percentage']}%)")
    

    db.close()
