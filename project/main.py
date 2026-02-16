
from flask import Flask, render_template, request, redirect, url_for, flash
from model import init_db, get_session, get_latest_poll_by_zipcode, get_poll_by_id, add_vote, get_poll_results
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)