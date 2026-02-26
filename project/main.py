from flask import Flask, render_template, request, redirect, url_for, flash, session
from model import (
    init_db, get_session, 
    get_latest_poll_by_zipcode, 
    get_poll_by_id, 
    add_vote, 
    get_poll_results, 
    get_all_polls,
    Poll,  
    Vote,
    Admin,
    ZipCode,  
    search_by_city_or_zip, 
    get_polls_by_zipcodes   
)
import os
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = 'test'

engine = init_db('sqlite:///polling.db')

def get_db():
    return get_session(engine)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

''' Original code for index page, can be uncommented if needed
@app.route('/', methods=['GET', 'POST'])
def index():
    
    if request.method == 'POST':
        # Get zip code from form
        zip_code = request.form.get('zip_code', '').strip()
        
        # validation
        if not zip_code:
            flash('Please enter a zip code', 'error')
            return redirect(url_for('index'))
        
        if not zip_code.isdigit():
            flash('Zip code must be numeric', 'error')
            return redirect(url_for('index'))
        
        if len(zip_code) != 5:
            flash('Zip code must be 5 digits', 'error')
            return redirect(url_for('index'))
        db = get_db()
        poll = get_latest_poll_by_zipcode(db, zip_code)
        db.close()
        
        if poll:
            return redirect(url_for('poll_page', poll_id=poll.id))
        else:
            flash(f'No {zip_code} Poll Found', 'error')
            return redirect(url_for('index'))
    
    return render_template('index.html')
'''
@app.route('/', methods=['GET', 'POST'])
def index():

    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        

        if not query:
            flash('Please enter a zip code or city name', 'error')
            return redirect(url_for('index'))
        
        db = get_db()
        
        if query.isdigit() and len(query) == 5:
            poll = get_latest_poll_by_zipcode(db, query)
            db.close()
            
            if poll:
                return redirect(url_for('poll_page', poll_id=poll.id))
            else:
                flash(f'No poll found for zip code {query}', 'error')
                return redirect(url_for('index'))
        
        else:
            zipcodes = search_by_city_or_zip(db, query)
            
            if not zipcodes:
                flash(f'City "{query}" not found', 'error')
                db.close()
                return redirect(url_for('index'))

            zip_list = [zc.zip_code for zc in zipcodes]
            polls = get_polls_by_zipcodes(db, zip_list)
            
            db.close()
            
            if not polls:
                flash(f'City "{query}" poll not found', 'error')
                return redirect(url_for('index'))
            

            if len(polls) == 1:
                return redirect(url_for('poll_page', poll_id=polls[0].id))

            return render_template('select_poll.html', 
                                 query=query, 
                                 polls=polls,
                                 zipcodes=zipcodes)
    
    return render_template('index.html')


@app.route('/poll/<int:poll_id>')  
def poll_page(poll_id):     
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    db.close()
    
    if not poll:
        flash('Poll does not exist', 'error')
        return redirect(url_for('index'))
    return render_template('poll.html', poll=poll)


@app.route('/poll/<int:poll_id>/vote', methods=['POST'])
def submit_vote(poll_id):
    
    choice = request.form.get('choice')
    
    if choice is None:
        flash('Please select an option', 'error')
        return redirect(url_for('poll_page', poll_id=poll_id))
    
    db = get_db()
    
    try:
        add_vote(db, poll_id, int(choice))
        flash('Vote submitted successfully!', 'success')
    except Exception as e:
        flash(f'Vote failed: {str(e)}', 'error')
        db.rollback()
    finally:
        db.close()
    
    return redirect(url_for('index'))
''' Originial code for results page, can be uncommented if needed
@app.route('/poll/<int:poll_id>/results')
def poll_results(poll_id):
    
    db = get_db()
    data = get_poll_results(db, poll_id)
    db.close()
    
    if not data:
        flash('Poll does not exist', 'error')
        return redirect(url_for('index'))
    
    return render_template(
        'results.html',
        poll=data['poll'],
        results=data['results'],
        total_votes=data['total_votes']
    )
'''  
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('admin_login'))
        
        db = get_db()
        admin = db.query(Admin).filter_by(username=username).first()
        db.close()
        
        if admin and admin.password_hash == hash_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username or password is incorrect', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))



  
@app.route('/admin')
@login_required
def admin_dashboard():
    
    db = get_db()
    polls = get_all_polls(db)
    
    total_polls = len(polls)
    total_votes_count = db.query(Vote).count()
    active_polls = db.query(Poll).filter_by(is_active=1).count()
    
    db.close()
    
    return render_template(
        'admin/dashboard.html',
        polls=polls,
        total_polls=total_polls,
        total_votes_count=total_votes_count,
        active_polls=active_polls
    )
    
@app.route('/admin/poll/<int:poll_id>')
@login_required
def admin_poll_detail(poll_id):    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    if not poll:
        flash('No poll', 'error')
        return redirect(url_for('admin_dashboard'))

    data = get_poll_results(db, poll_id)

    votes = db.query(Vote).filter_by(poll_id=poll_id).order_by(Vote.voted_at.desc()).all()
    
    db.close()
    
    return render_template(
        'admin/poll_detail.html',
        poll=poll,
        results=data['results'],
        total_votes=data['total_votes'],
        votes=votes
    )
@app.route('/admin/poll/create', methods=['GET', 'POST'])
@login_required
def admin_create_poll():
    
    if request.method == 'POST':
        zip_code = request.form.get('zip_code', '').strip()
        title = request.form.get('title', '').strip()
        question = request.form.get('question', '').strip()
        
        options = []
        for i in range(1, 11): 
            option = request.form.get(f'option_{i}', '').strip()
            if option:
                options.append(option)
        

        if not zip_code or not title or not question:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('admin_create_poll'))
        
        if len(options) < 2:
            flash('At least 2 options are required', 'error')
            return redirect(url_for('admin_create_poll'))
        
        db = get_db()
        try:
            poll = Poll(
                zip_code=zip_code,
                title=title,
                question=question
            )
            poll.set_options(options)
            db.add(poll)
            db.commit()
            
            flash(f'Poll created successfully! Poll ID: {poll.id}', 'success')
            return redirect(url_for('admin_poll_detail', poll_id=poll.id))
        except Exception as e:
            flash(f'Creation failed: {str(e)}', 'error')
            db.rollback()
        finally:
            db.close()
    
    return render_template('admin/create_poll.html')

@app.route('/admin/poll/<int:poll_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_poll(poll_id):
    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll does not exist', 'error')
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':

        poll.zip_code = request.form.get('zip_code', '').strip()
        poll.title = request.form.get('title', '').strip()
        poll.question = request.form.get('question', '').strip()
        poll.is_active = int(request.form.get('is_active', 1))
        
        options = []
        for i in range(1, 11):
            option = request.form.get(f'option_{i}', '').strip()
            if option:
                options.append(option)
        
        if len(options) >= 2:
            poll.set_options(options)
        
        try:
            db.commit()
            flash('Poll updated successfully!', 'success')
            return redirect(url_for('admin_poll_detail', poll_id=poll_id))
        except Exception as e:
            flash(f'Update failed: {str(e)}', 'error')
            db.rollback()
        finally:
            db.close()
    
    db.close()
    return render_template('admin/edit_poll.html', poll=poll)

@app.route('/admin/poll/<int:poll_id>/delete', methods=['POST'])
@login_required
def admin_delete_poll(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll does not exist', 'error')
    else:
        try:
            db.delete(poll)
            db.commit()
            flash(f'Poll "{poll.title}" has been deleted', 'success')
        except Exception as e:
            flash(f'Delete failed: {str(e)}', 'error')
            db.rollback()
    
    db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/poll/<int:poll_id>/toggle', methods=['POST'])
@login_required
def admin_toggle_poll(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll does not exist', 'error')
    else:
        try:
            poll.is_active = 0 if poll.is_active == 1 else 1
            db.commit()
            status = "activated" if poll.is_active == 1 else "deactivated"
            flash(f'Poll has been {status}', 'success')
        except Exception as e:
            flash(f'Operation failed: {str(e)}', 'error')
            db.rollback()
    
    db.close()
    return redirect(url_for('admin_dashboard'))
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)