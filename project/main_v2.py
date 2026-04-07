# app_v2.py - Flask Application V2 (supports multiple poll types)
import csv
from io import StringIO
from flask import make_response
from flask import Flask, render_template, request, redirect, url_for, flash, session
from model_v2 import (
    init_db, get_session, 
    get_polls_by_zipcode, 
    get_polls_by_city,
    get_poll_by_id, 
    get_poll_results, 
    get_all_polls,
    add_vote_single_choice,
    add_vote_multiple_choice,
    add_vote_rating,
    add_vote_ranked,
    get_zipcodes_by_city,
    search_by_city_or_zip,
    Poll,
    Vote,
    Admin,
    ZipCode,
    poll_zipcodes,
    poll_districts
)

from model_v2 import School, search_schools, get_zipcodes_by_district
from sqlalchemy import func
import os
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'polling-system-secret-key-v2-2026')





engine = init_db('sqlite:///polling_v2.db')

def get_db():

    return get_session(engine)




def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page: enter zip code, city name, or school district name to find polls"""
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        if not query:
            flash('Please enter a zip code, city, or school district name', 'error')
            return redirect(url_for('index'))
        
        db = get_db()
        polls = []
        
        # Strategy 1: if it's a 5-digit number, treat as zip code
        if query.isdigit() and len(query) == 5:
            print(f"Searching by zipcode: {query}")
            polls = get_polls_by_zipcode(db, query)
            if polls:
                print(f"Found {len(polls)} polls by zipcode")
        
        # Strategy 2: try searching by district name (direct association)
        if not polls:
            print(f"Searching by district: {query}")
            
            # Find matching districts
            districts = db.query(School).filter(
                School.district.ilike(f'%{query}%'),
                School.record_type == 'District'
            ).all()
            
            print(f"Found {len(districts)} districts")
            
            if districts:
                # New logic: find polls directly linked to this district
                district_ids = [d.id for d in districts]
                
                poll_ids = db.query(poll_districts.c.poll_id).filter(
                    poll_districts.c.district_id.in_(district_ids)
                ).distinct().all()
                
                poll_id_list = [p[0] for p in poll_ids]
                print(f"Found {len(poll_id_list)} polls directly linked to districts")
                
                if poll_id_list:
                    polls = db.query(Poll).filter(
                        Poll.id.in_(poll_id_list),
                        Poll.is_active == 1
                    ).all()
                    print(f"Found {len(polls)} active polls")
        
        # Strategy 3: try searching by city
        if not polls:
            print(f"Searching by city: {query}")
            
            if ',' in query:
                parts = query.split(',')
                city = parts[0].strip()
                state = parts[1].strip() if len(parts) > 1 else None
            else:
                city = query
                state = None
            
            polls = get_polls_by_city(db, city, state)
            print(f"Found {len(polls)} polls by city")
        
        db.close()
        
        if not polls:
            flash(f'No polls found for "{query}"', 'error')
            return redirect(url_for('index'))
        
        if len(polls) == 1:
            return redirect(url_for('poll_page', poll_id=polls[0].id))
        
        return render_template('select_poll.html', 
                             query=query, 
                             polls=polls)
    
    return render_template('index.html')





@app.route('/poll/<int:poll_id>')
def poll_page(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    db.close()
    
    if not poll:
        flash('Poll not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('poll_v2.html', poll=poll)




@app.route('/poll/<int:poll_id>/vote', methods=['POST'])
def submit_vote(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
        db.close()
        return redirect(url_for('index'))
    
    try:
        user_id = 0  
        

        if poll.poll_type == 'single_choice':
            choice = request.form.get('choice')
            if choice is None:
                flash('Please select an option', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            add_vote_single_choice(db, poll_id, int(choice), user_id)
        
        elif poll.poll_type == 'multiple_choice':
            choices = request.form.getlist('choices')
            if not choices:
                flash('Please select at least one option', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            choices = [int(c) for c in choices]
            

            if len(choices) < poll.min_choices:
                flash(f'Please select at least {poll.min_choices} option(s)', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            if poll.max_choices and len(choices) > poll.max_choices:
                flash(f'Please select at most {poll.max_choices} option(s)', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            add_vote_multiple_choice(db, poll_id, choices, user_id)
        
        elif poll.poll_type == 'rating_scale':
            rating = request.form.get('rating')
            if rating is None:
                flash('Please select a rating', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            rating = int(rating)
            
            if rating < poll.rating_min or rating > poll.rating_max:
                flash(f'Rating must be between {poll.rating_min} and {poll.rating_max}', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            add_vote_rating(db, poll_id, rating, user_id)
        
        elif poll.poll_type == 'ranked_choice':
            ranking = request.form.get('ranking')
            if not ranking:
                flash('Please rank all options', 'error')
                db.close()
                return redirect(url_for('poll_page', poll_id=poll_id))
            
            import json
            ranking = json.loads(ranking)
            
            add_vote_ranked(db, poll_id, ranking, user_id)
        
        flash('Vote submitted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error submitting vote: {str(e)}', 'error')
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
        flash('Poll not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('results_v2.html', data=data)




@app.route('/api/autocomplete')
def autocomplete():

    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return {'results': []}
    
    db = get_db()
    results = []
    
    if query.isdigit():
        zipcodes = db.query(ZipCode).filter(
            ZipCode.zip_code.like(f'{query}%')
        ).limit(10).all()
        
        for zc in zipcodes:
            results.append({
                'type': 'zipcode',
                'display': f"{zc.zip_code} - {zc.city}, {zc.state}",
                'value': zc.zip_code,
            })
    else:
        cities = db.query(
            ZipCode.city, 
            ZipCode.state
        ).filter(
            ZipCode.city.ilike(f'{query}%')
        ).distinct().limit(10).all()
        
        city_counts = {}
        for city, state in cities:
            city_counts[city] = city_counts.get(city, 0) + 1
        
        for city, state in cities:
            if city_counts[city] > 1:
                value = f"{city}, {state}"
                display = f"{city}, {state}"
            else:
                value = city
                display = f"{city}, {state}"
            
            results.append({
                'type': 'city',
                'display': display,
                'value': value,
            })
    
    db.close()
    
    return {'results': results}



@app.route('/api/search-cities')
def search_cities():

    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return {'cities': []}
    
    db = get_db()
    

    cities = db.query(
        ZipCode.city,
        ZipCode.state,
        func.count(ZipCode.id).label('zipcode_count')
    ).filter(
        ZipCode.city.ilike(f'{query}%')
    ).group_by(
        ZipCode.city, ZipCode.state
    ).limit(10).all()
    
    results = [
        {
            'city': city,
            'state': state,
            'zipcode_count': count
        }
        for city, state, count in cities
    ]
    
    db.close()
    
    return {'cities': results}




@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():

    
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter username and password', 'error')
            return redirect(url_for('admin_login'))
        
        db = get_db()
        admin = db.query(Admin).filter_by(username=username).first()
        db.close()
        
        if admin and admin.password_hash == hash_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash(f'Welcome back, {admin.username}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(' Invalid username or password', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():

    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():

    
    db = get_db()
    

    polls_with_votes = db.query(
        Poll,
        func.count(Vote.id).label('vote_count')
    ).outerjoin(
        Vote, Poll.id == Vote.poll_id
    ).group_by(
        Poll.id
    ).order_by(
        Poll.created_at.desc()
    ).all()
    
    polls_data = [
        {'poll': poll, 'vote_count': vote_count}
        for poll, vote_count in polls_with_votes
    ]
    
    total_polls = len(polls_data)
    total_votes_count = db.query(Vote).count()
    active_polls = db.query(Poll).filter_by(is_active=1).count()
    
    db.close()
    
    return render_template(
        'admin/dashboard.html',
        polls_data=polls_data,
        total_polls=total_polls,
        total_votes_count=total_votes_count,
        active_polls=active_polls
    )




# app_v2.py - Modify poll creation logic

@app.route('/admin/poll/create', methods=['GET', 'POST'])
@login_required
def admin_create_poll():
    """Create a new poll"""
    
    if request.method == 'POST':
        import json
        
        db = get_db()
        
        try:
            # Basic information
            title = request.form.get('title', '').strip()
            question = request.form.get('question', '').strip()
            description = request.form.get('description', '').strip()
            poll_type = request.form.get('poll_type', 'single_choice')
            
            if not title or not question:
                flash('Title and question are required', 'error')
                return redirect(url_for('admin_create_poll'))
            
            # Create poll object
            poll = Poll(
                title=title,
                question=question,
                description=description,
                poll_type=poll_type
            )
            
            # Set options and configuration based on type
            if poll_type in ['single_choice', 'multiple_choice', 'ranked_choice']:
                options = []
                for key in request.form:
                    if key.startswith('option_'):
                        option = request.form[key].strip()
                        if option:
                            options.append(option)
                
                if len(options) < 2:
                    flash('At least 2 options are required', 'error')
                    db.close()
                    return redirect(url_for('admin_create_poll'))
                
                poll.set_options(options)
                
                if poll_type == 'multiple_choice':
                    poll.min_choices = int(request.form.get('min_choices', 1))
                    max_choices = request.form.get('max_choices', '')
                    poll.max_choices = int(max_choices) if max_choices else None
            
            elif poll_type == 'rating_scale':
                poll.rating_min = int(request.form.get('rating_min', 1))
                poll.rating_max = int(request.form.get('rating_max', 5))
                
                label_min = request.form.get('rating_label_min', '').strip()
                label_max = request.form.get('rating_label_max', '').strip()
                
                if label_min or label_max:
                    labels = {}
                    if label_min:
                        labels[str(poll.rating_min)] = label_min
                    if label_max:
                        labels[str(poll.rating_max)] = label_max
                    poll.set_rating_labels(labels)
            
            # Handle geographic location
            zipcodes_json = request.form.get('zipcodes', '[]')
            cities_json = request.form.get('cities', '[]')
            districts_json = request.form.get('districts', '[]')  # New: get district data
            
            selected_zipcodes = json.loads(zipcodes_json)
            selected_cities = json.loads(cities_json)
            selected_districts = json.loads(districts_json)  # New
            
            if not selected_zipcodes and not selected_cities and not selected_districts:
                flash('Please select at least one zip code, city, or school district', 'error')
                db.close()
                return redirect(url_for('admin_create_poll'))
            
            # Collect all zip code objects
            zipcode_objects = []
            cities_list = []
            states_list = set()
            
            # Add directly selected zip codes
            for zip_code in selected_zipcodes:
                zc = db.query(ZipCode).filter_by(zip_code=zip_code).first()
                
                if not zc:
                    school = db.query(School).filter_by(zip_code=zip_code).first()
                    if school:
                        zc = ZipCode(
                            zip_code=zip_code,
                            city=school.city,
                            state='CA',
                            county=school.county
                        )
                        db.add(zc)
                        db.flush()
                
                if zc:
                    zipcode_objects.append(zc)
                    cities_list.append({"city": zc.city, "state": zc.state})
                    states_list.add(zc.state)
            
            # Add all zip codes for selected cities
            for city_data in selected_cities:
                city = city_data['city']
                state = city_data['state']
                
                zipcodes = db.query(ZipCode).filter_by(
                    city=city,
                    state=state
                ).all()
                
                for zc in zipcodes:
                    if zc not in zipcode_objects:
                        zipcode_objects.append(zc)
                
                cities_list.append({"city": city, "state": state})
                states_list.add(state)
            
            # New: handle district associations
            district_objects = []
            
            for district_data in selected_districts:
                district_name = district_data['district']
                
                # Find district (only search for District type)
                district = db.query(School).filter(
                    School.district == district_name,
                    School.record_type == 'District'
                ).first()
                
                if district:
                    district_objects.append(district)
                    
                    # Get zip codes for the district
                    district_zipcodes = db.query(School.zip_code).filter(
                        School.district == district_name,
                        School.zip_code.isnot(None)
                    ).distinct().all()
                    
                    for (zip_code,) in district_zipcodes:
                        zc = db.query(ZipCode).filter_by(zip_code=zip_code).first()
                        
                        if not zc:
                            school = db.query(School).filter_by(zip_code=zip_code).first()
                            if school:
                                zc = ZipCode(
                                    zip_code=zip_code,
                                    city=school.city,
                                    state='CA',
                                    county=school.county
                                )
                                db.add(zc)
                                db.flush()
                        
                        if zc and zc not in zipcode_objects:
                            zipcode_objects.append(zc)
                            cities_list.append({"city": zc.city, "state": zc.state})
                            states_list.add(zc.state)
            
            # Associate zip codes
            poll.zipcodes.extend(zipcode_objects)
            
            # New: associate districts
            poll.districts.extend(district_objects)
            
            # Set city and state information
            poll.set_cities(cities_list)
            poll.set_states(list(states_list))
            
            db.add(poll)
            db.commit()
            
            flash(f'Poll "{title}" created successfully!', 'success')
            return redirect(url_for('admin_poll_results', poll_id=poll.id))
        
        except Exception as e:
            flash(f'Error creating poll: {str(e)}', 'error')
            db.rollback()
            db.close()
            return redirect(url_for('admin_create_poll'))
    
    return render_template('admin/create_poll_v2.html')
# ============================================
# Admin: Poll Detail (redirect to results page)
# ============================================

@app.route('/admin/poll/<int:poll_id>')
@login_required
def admin_poll_detail(poll_id):
    """View poll detail - redirect to admin results page"""
    # Directly redirect to admin_poll_results
    return redirect(url_for('admin_poll_results', poll_id=poll_id))


# ============================================
# Admin: View Results (Admin style)
# ============================================

@app.route('/admin/poll/<int:poll_id>/results')
@login_required
def admin_poll_results(poll_id):
    """Admin view poll results (Admin style)"""
    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    # Get results
    data = get_poll_results(db, poll_id)
    
    # Get recent vote records
    votes = db.query(Vote).filter_by(poll_id=poll_id).order_by(Vote.voted_at.desc()).limit(20).all()
    
    # Preload data
    zipcodes_list = [(zc.zip_code, zc.city, zc.state) for zc in poll.zipcodes]
    cities = poll.get_cities()
    states = poll.get_states()
    
    db.close()
    
    # Render Admin style results page
    return render_template(
        'admin/poll_results.html',
        poll=poll,
        results=data['results'],
        total_votes=data['total_votes'],
        votes=votes,
        zipcodes_list=zipcodes_list,
        cities=cities,
        states=states
    )

# app_v2.py - Add edit poll route

@app.route('/admin/poll/<int:poll_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_poll(poll_id):
    """Edit poll"""
    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            # Update basic information
            poll.title = request.form.get('title', '').strip()
            poll.question = request.form.get('question', '').strip()
            poll.description = request.form.get('description', '').strip()
            poll.is_active = int(request.form.get('is_active', 1))
            
            # Update options based on type
            if poll.poll_type in ['single_choice', 'multiple_choice', 'ranked_choice']:
                options = []
                i = 1
                while True:
                    option_key = f'option_{i}'
                    if option_key in request.form:
                        option = request.form[option_key].strip()
                        if option:
                            options.append(option)
                        i += 1
                    else:
                        break
                
                if len(options) >= 2:
                    poll.set_options(options)
                else:
                    flash('At least 2 options are required', 'error')
                    db.close()
                    return redirect(url_for('admin_edit_poll', poll_id=poll_id))
                
                # Multiple choice configuration
                if poll.poll_type == 'multiple_choice':
                    poll.min_choices = int(request.form.get('min_choices', 1))
                    max_choices = request.form.get('max_choices', '')
                    poll.max_choices = int(max_choices) if max_choices else None
            
            elif poll.poll_type == 'rating_scale':
                poll.rating_min = int(request.form.get('rating_min', 1))
                poll.rating_max = int(request.form.get('rating_max', 5))
                
                label_min = request.form.get('rating_label_min', '').strip()
                label_max = request.form.get('rating_label_max', '').strip()
                
                if label_min or label_max:
                    labels = {}
                    if label_min:
                        labels[str(poll.rating_min)] = label_min
                    if label_max:
                        labels[str(poll.rating_max)] = label_max
                    poll.set_rating_labels(labels)
            
            db.commit()
            flash('Poll updated successfully!', 'success')
            db.close()
            return redirect(url_for('admin_poll_detail', poll_id=poll_id))
        
        except Exception as e:
            flash(f'Error updating poll: {str(e)}', 'error')
            db.rollback()
            db.close()
            return redirect(url_for('admin_edit_poll', poll_id=poll_id))
    
    # GET request: preload all required data
    zipcodes_list = [zc.zip_code for zc in poll.zipcodes]
    cities = poll.get_cities()
    states = poll.get_states()
    
    db.close()
    
    return render_template(
        'admin/edit_poll_v2.html', 
        poll=poll,
        zipcodes_list=zipcodes_list,
        cities=cities,
        states=states
    )


@app.route('/admin/poll/<int:poll_id>/delete', methods=['POST'])
@login_required
def admin_delete_poll(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
    else:
        try:
            db.delete(poll)
            db.commit()
            flash(f' Poll "{poll.title}" deleted', 'success')
        except Exception as e:
            flash(f' Error deleting poll: {str(e)}', 'error')
            db.rollback()
    
    db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/poll/<int:poll_id>/toggle', methods=['POST'])
@login_required
def admin_toggle_poll(poll_id):

    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
    else:
        try:
            poll.is_active = 0 if poll.is_active == 1 else 1
            db.commit()
            status = "activated" if poll.is_active == 1 else "deactivated"
            flash(f' Poll {status}', 'success')
        except Exception as e:
            flash(f' Error: {str(e)}', 'error')
            db.rollback()
    
    db.close()
    return redirect(url_for('admin_dashboard'))




@app.errorhandler(404)
def not_found(e):
    flash('Page not found', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def server_error(e):
    flash(f'Server error: {str(e)}', 'error')
    return redirect(url_for('index'))





# ============================================
# Admin: Export Poll Data as CSV
# ============================================

@app.route('/admin/poll/<int:poll_id>/export')
@login_required
def export_poll_csv(poll_id):
    """Export poll data as CSV"""
    
    db = get_db()
    poll = get_poll_by_id(db, poll_id)
    
    if not poll:
        flash('Poll not found', 'error')
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    # Get all vote records
    votes = db.query(Vote).filter_by(poll_id=poll_id).order_by(Vote.voted_at).all()
    
    # Preload zip code information
    zipcodes_list = [(zc.zip_code, zc.city, zc.state) for zc in poll.zipcodes]
    
    # Create CSV
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header information
    writer.writerow(['Poll Export'])
    writer.writerow(['Poll ID', poll.id])
    writer.writerow(['Title', poll.title])
    writer.writerow(['Question', poll.question])
    writer.writerow(['Type', poll.poll_type])
    writer.writerow(['Created', poll.created_at.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Total Votes', len(votes)])
    writer.writerow([])
    
    # Write vote data
    if poll.poll_type == 'single_choice':
        writer.writerow(['Vote ID', 'Choice', 'Voted At'])
        options = poll.get_options()
        for vote in votes:
            writer.writerow([
                vote.id,
                options[vote.choice],
                vote.voted_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif poll.poll_type == 'multiple_choice':
        writer.writerow(['Vote ID', 'Choices', 'Voted At'])
        options = poll.get_options()
        for vote in votes:
            choices = vote.get_choices()
            choice_names = [options[i] for i in choices]
            writer.writerow([
                vote.id,
                ', '.join(choice_names),
                vote.voted_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif poll.poll_type == 'rating_scale':
        writer.writerow(['Vote ID', 'Rating', 'Voted At'])
        for vote in votes:
            writer.writerow([
                vote.id,
                vote.rating,
                vote.voted_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif poll.poll_type == 'ranked_choice':
        writer.writerow(['Vote ID', 'Ranking', 'Voted At'])
        options = poll.get_options()
        for vote in votes:
            ranking = vote.get_ranking()
            ranked_names = [options[i] for i in ranking]
            writer.writerow([
                vote.id,
                ' > '.join(ranked_names),
                vote.voted_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    # Add statistics summary
    writer.writerow([])
    writer.writerow(['Summary'])
    
    if poll.poll_type in ['single_choice', 'multiple_choice']:
        writer.writerow(['Option', 'Vote Count', 'Percentage'])
        data = get_poll_results(db, poll_id)
        for option, stats in data['results'].items():
            writer.writerow([option, stats['count'], f"{stats['percentage']}%"])
    
    elif poll.poll_type == 'rating_scale':
        data = get_poll_results(db, poll_id)
        writer.writerow(['Average Rating', data['results']['average']])
        writer.writerow([])
        writer.writerow(['Rating', 'Count'])
        for rating, count in data['results']['ratings'].items():
            writer.writerow([rating, count])
    
    db.close()
    
    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=poll_{poll_id}_export.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

@app.route('/api/search-schools')
def api_search_schools():
    """
    Search district API
    Supports: district name, city name, county name, zip code
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return {'schools': []}
    
    db = get_db()
    
    # Search districts (only return District type)
    schools = db.query(School).filter(
        School.record_type == 'District',
        (School.district.ilike(f'%{query}%')) |
        (School.city.ilike(f'%{query}%')) |
        (School.county.ilike(f'%{query}%'))
    ).limit(15).all()
    
    results = []
    for school in schools:
        # Count the number of zip codes for this district
        zipcodes = db.query(School.zip_code).filter(
            School.district == school.district,
            School.zip_code.isnot(None)
        ).distinct().all()
        
        zipcode_count = len(zipcodes)
        
        results.append({
            'district': school.district,
            'county': school.county,
            'city': school.city,
            'zip_code': school.zip_code,
            'zipcode_count': zipcode_count,
            'cds_code': school.cds_code
        })
    
    db.close()
    
    return {'schools': results}


@app.route('/api/get-district-zipcodes')
def api_get_district_zipcodes():
    """
    Get all zip codes by district name
    """
    district_name = request.args.get('district', '').strip()
    
    if not district_name:
        return {'zipcodes': []}
    
    db = get_db()
    
    # Get all zip codes for this district
    zipcodes_data = db.query(
        School.zip_code,
        School.city
    ).filter(
        School.district == district_name,
        School.zip_code.isnot(None)
    ).distinct().all()
    
    # Convert to list of dictionaries
    zipcodes = [
        {
            'zip_code': zc,
            'city': city
        }
        for zc, city in zipcodes_data
    ]
    
    db.close()
    
    return {'zipcodes': zipcodes}


if __name__ == '__main__':    
    app.run(debug=True, host='0.0.0.0', port=5000)
    
    