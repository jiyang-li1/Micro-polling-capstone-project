from model import init_db, get_session, Poll, get_latest_poll_by_zipcode
from datetime import datetime



engine = init_db('sqlite:///polling.db')
db = get_session(engine)


deleted_polls = db.query(Poll).delete()
db.commit()



polls_data = [
    
    {
        "zip_code": "11111",
        "title": "Test Poll1",
        "question": "Test question1",
        "options": ["Option A", "Option B", "Option C"],
        "created_at": datetime(2025, 1, 1, 1, 1, 1)  
    },
    {
        "zip_code": "11111",
        "title": "Test Poll2",
        "question": "Test question2",
        "options": ["Yes", "No"],
        "created_at": datetime(2025, 2, 2, 2, 2, 2)  
    },
    {
        "zip_code": "11111",
        "title": "Test Poll3", 
        "question": "Test question3",
        "options": ["A", "B", "C", "D"],
        "created_at": datetime(2026, 1, 1, 1, 1, 1)  
    },
    
    # 邮编 10001 的投票（Manhattan, NY）
    {
        "zip_code": "22222",
        "title": "Test Poll4",
        "question": "Test question4",
        "options": ["Yes", "No"],
        "created_at": datetime(2026, 1, 1, 1, 1, 1)
    },
    {
        "zip_code": "22222",
        "title": "Test Poll5",  # 🔴 最新的！
        "question": "Test question5",
        "options": ["Yes", "No", "Need More Info"],
        "created_at": datetime(2026, 2, 2, 2, 2, 2)
    },
    
    {
        "zip_code": "33333",
        "title": "Test Poll6",
        "question": "Test question6",
        "options": ["A", "B", "C", "D"],
        "created_at": datetime(2026, 1, 1, 1, 1, 1)
    },
    

    {
        "zip_code": "44444",
        "title": "Test Poll7",
        "question": "Test question7",
        "options": ["Yes", "No"],
        "created_at": datetime(2026, 1, 1, 1, 1, 1)
    },
    {
        "zip_code": "55555",
        "title": "Test Poll8",
        "question": "Test question8",
        "options": ["Yes", "No", "Undecided"],
        "created_at": datetime(2026, 1, 1, 1, 1, 1)
    }
]


for poll_data in polls_data:
    poll = Poll(
        zip_code=poll_data["zip_code"],
        title=poll_data["title"],
        question=poll_data["question"],
        created_at=poll_data["created_at"]
    )
    poll.set_options(poll_data["options"])
    db.add(poll)

db.commit()

