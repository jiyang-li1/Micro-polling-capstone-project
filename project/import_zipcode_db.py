import csv
from model import init_db, get_session, Base
from sqlalchemy import Column, Integer, String, Index

class ZipCode(Base):
    __tablename__ = 'zipcodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zip_code = Column(String(10), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(2), nullable=False, index=True)

    __table_args__ = (
        Index('idx_city_state', 'city', 'state'),
    )
    
    def __repr__(self):
        return f"<ZipCode(zip={self.zip_code}, city='{self.city}', state='{self.state}')>"




engine = init_db('sqlite:///polling.db')
db = get_session(engine)


Base.metadata.create_all(engine)



db.query(ZipCode).delete()
db.commit()


csv_file = './../ZIP_Locale_Detail.csv'


try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            zipcode = ZipCode(
                zip_code=row['DELIVERY ZIPCODE'].strip(),
                city=row['PHYSICAL CITY'].strip(),
                state=row['PHYSICAL STATE'].strip()
            )
            db.add(zipcode)
            count += 1
            
            if count % 1000 == 0:
                db.commit()

        db.commit()

        
except FileNotFoundError:
    print("File not found")

except Exception as e:
    print("An error occurred:", e)
    db.rollback()


total = db.query(ZipCode).count()
states = db.query(ZipCode.state).distinct().count()
cities = db.query(ZipCode.city).distinct().count()

print("total zip codes:", total)
print("total states:", states)
print("total cities:", cities)



samples = db.query(ZipCode).limit(10).all()
for zc in samples:
    print(f"  {zc.zip_code:6s} → {zc.city:20s}, {zc.state}")

db.close()
