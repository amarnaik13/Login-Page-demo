import os
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for, flash, render_template
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import sys
import io
import time
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import tempfile
from models import User, db
from forms import LoginForm, RegistrationForm
from utils import load_data, to_excel, highlighter, get_name, initialize_session_state
from backend import get_results
from ast import literal_eval

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

import warnings
warnings.filterwarnings('ignore')

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize extensions
CORS(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Initialize session state
initialize_session_state()

# Create all database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_files():
    try:
        rr_file = request.files['file1']
        bench_file = request.files['file2']
        isCvSkills = request.form.get('isCvSkills') == 'true'
        
        rr_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        bench_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        print(f"isCvSkills: {isCvSkills}")
        rr_file.save(rr_temp.name)
        bench_file.save(bench_temp.name)
        
        rr_df = load_data(rr_temp.name)
        bench_data = load_data(bench_temp.name)

        # Making API calls for generation        
        get_results(rr_df, bench_data, isCvSkills)

        # Simulate processing time
        time.sleep(5)

        # Return success response with temporary file paths
        return jsonify({"file1": rr_temp.name, "file2": bench_temp.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/recommendations/rr', methods=['GET'])
@login_required
def get_recommendations_by_rr():
    try:
        bench_data = load_data(request.args.get('bench_file'))
        rr_file = load_data(request.args.get('rr_file'))

        refined_rr_df = pd.read_excel(r"assets/output/refined_RR_To_Profiles_Recommendations.xlsx")
        refined_rr_df.drop(["uuid"], axis=1, inplace=True)

        def remove_list(x):
            return ", ".join(literal_eval(x))

        refined_rr_df["RR Skills"] = refined_rr_df["RR Skills"].apply(remove_list)
        refined_rr_df["Candidate_Skills"] = refined_rr_df["Candidate_Skills"].apply(remove_list)
        refined_rr_df["matched_skillset"] = refined_rr_df["matched_skillset"].apply(remove_list)
        refined_rr_df["recommended_trainings"] = refined_rr_df["recommended_trainings"].apply(remove_list)

        refined_rr_df["RR"] = refined_rr_df["RR"].astype(str)
        refined_rr_df["portal_id"] = refined_rr_df["portal_id"].astype(str)
        refined_rr_df["Employee Name"] = refined_rr_df["portal_id"].apply(lambda pid: get_name(pid, bench_data))
        refined_rr_df["bench_period"] = refined_rr_df["bench_period"].astype(str)
        refined_rr_df["Score"] = round(refined_rr_df["Score"] * 100)

        refined_rr_df.rename(columns={
            'Candidate_Skills': 'Overall Employee Skills',
            'Score': 'Match Score',
            'bench_period': 'Bench Period',
            'matched_skillset': 'Matched Skills',
            'portal_id': 'Portal ID',
            'recommended_trainings': 'Recommended Trainings',
        }, inplace=True)

        rr_cols = ['RR', 'RR Skills', 'Portal ID', 'Employee Name', 'Overall Employee Skills', 'Matched Skills', 'Recommended Trainings', 'Match Score', 'Bench Period','Profile Link']
        styled_rr_df = refined_rr_df[rr_cols]

        return jsonify(styled_rr_df.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/recommendations/profiles', methods=['GET'])
@login_required
def get_recommendations_by_profiles():
    try:
        bench_data = load_data(request.args.get('bench_file'))
        rr_file = load_data(request.args.get('rr_file'))

        refined_profile_df = pd.read_excel(r"assets/output/refined_Profiles_To_RR_Recommendations.xlsx")
        refined_profile_df.drop(["uuid"], axis=1, inplace=True)

        def remove_list(x):
            return ", ".join(literal_eval(x))

        refined_profile_df["RR Skills"] = refined_profile_df["RR Skills"].apply(remove_list)
        refined_profile_df["Candidate Skills"] = refined_profile_df["Candidate Skills"].apply(remove_list)
        refined_profile_df["matched_skillset"] = refined_profile_df["matched_skillset"].apply(remove_list)
        refined_profile_df["recommended_trainings"] = refined_profile_df["recommended_trainings"].apply(remove_list)

        refined_profile_df["RR"] = refined_profile_df["RR"].astype(str)
        refined_profile_df["portal_id"] = refined_profile_df["portal_id"].astype(str)
        refined_profile_df["Employee Name"] = refined_profile_df["portal_id"].apply(lambda pid: get_name(pid, bench_data))
        refined_profile_df["Score"] = round(refined_profile_df["Score"] * 100)

        refined_profile_df.rename(columns={
            'Candidate Skills': 'Overall Employee Skills',
            'Score': 'Match Score',
            'matched_skillset': 'Matched Skills',
            'portal_id': 'Portal ID',
            'recommended_trainings': 'Recommended Trainings',
        }, inplace=True)

        profile_cols = ['Portal ID', 'Employee Name', 'Overall Employee Skills', 'RR', 'RR Skills', 'Matched Skills', 'Recommended Trainings', 'Match Score','Profile Link']
        styled_profile_df = refined_profile_df[profile_cols]

        return jsonify(styled_profile_df.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400