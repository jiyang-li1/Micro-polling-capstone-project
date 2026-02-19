from flask import Flask, render_template, request, redirect, url_for, flash
from model import (
    init_db, get_session, 
    get_latest_poll_by_zipcode, 
    get_poll_by_id, 
    add_vote, 
    get_poll_results, 
    get_all_polls,
    Poll,  
    Vote   
)
import os
app = Flask(__name__)
app.secret_key = 'test'

engine = init_db('sqlite:///polling.db')

def get_db():
    return get_session(engine)

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
    
@app.route('/admin')
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
def admin_toggle_poll(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('投票不存在', 'error')
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