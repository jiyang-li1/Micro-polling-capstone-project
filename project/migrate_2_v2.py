# migrate_to_v2.py - 从旧数据库迁移到新数据库

from model import init_db as init_db_v1, get_session as get_session_v1
from model import Poll as PollV1, Vote as VoteV1, ZipCode as ZipCodeV1, Admin as AdminV1
from model_v2 import init_db as init_db_v2, get_session as get_session_v2
from model_v2 import Poll as PollV2, Vote as VoteV2, ZipCode as ZipCodeV2, Admin as AdminV2




engine_v1 = init_db_v1('sqlite:///polling.db')
db_v1 = get_session_v1(engine_v1)


engine_v2 = init_db_v2('sqlite:///polling_v2.db')
db_v2 = get_session_v2(engine_v2)


zipcodes_v1 = db_v1.query(ZipCodeV1).all()
zipcode_map = {}  
for zc in zipcodes_v1:
    zc_v2 = ZipCodeV2(
        zip_code=zc.zip_code,
        city=zc.city,
        state=zc.state,
    )
    db_v2.add(zc_v2)
    db_v2.flush()  
    zipcode_map[zc.zip_code] = zc_v2

db_v2.commit()

'''
admins_v1 = db_v1.query(AdminV1).all()

for admin in admins_v1:
    admin_v2 = AdminV2(
        username=admin.username,
        password_hash=admin.password_hash,
        created_at=admin.created_at
    )
    db_v2.add(admin_v2)

db_v2.commit()
'''


polls_v1 = db_v1.query(PollV1).all()
poll_map = {}  

for poll in polls_v1:
    poll_v2 = PollV2(
        title=poll.title,
        question=poll.question,
        poll_type='single_choice', 
        created_at=poll.created_at,
        is_active=poll.is_active
    )
    poll_v2.set_options(poll.get_options())
    

    if poll.zip_code in zipcode_map:
        zipcode_obj = zipcode_map[poll.zip_code]
        poll_v2.zipcodes.append(zipcode_obj)
        

        poll_v2.set_cities([{"city": zipcode_obj.city, "state": zipcode_obj.state}])
        poll_v2.set_states([zipcode_obj.state])
    
    db_v2.add(poll_v2)
    db_v2.flush()
    poll_map[poll.id] = poll_v2

db_v2.commit()
print(f"{len(polls_v1)} Migrated Polls.")


print("\nMigrating votes...")
votes_v1 = db_v1.query(VoteV1).all()

for vote in votes_v1:
    if vote.poll_id in poll_map:
        vote_v2 = VoteV2(
            poll_id=poll_map[vote.poll_id].id,
            user_id=0,
            choice=vote.choice,
            voted_at=vote.voted_at
        )
        db_v2.add(vote_v2)

db_v2.commit()
print(f" {len(votes_v1)} Votes migrated.")

db_v1.close()
db_v2.close()

