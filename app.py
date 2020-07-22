#!/usr/bin/python

# -*- coding: utf-8 -*-

#__copyright__ = 'URHope'
# __Core Developers__= 'Zuhair, Sharique, Jino, Furqaan'

from __future__ import print_function
from config import host, username, password, db_name, urhope_mail, urhope_pass
from flask import Flask, render_template, redirect, url_for, request, g
from flask import session, abort, flash, jsonify
from flask_sslify import SSLify
from flask_caching import Cache
from flask_mysqlpool import MySQLPool
import json
import os
import datetime
import pymysql
import requests
import socket
import os.path
import flask
import urllib.request
import logging
import string
import random
import smtplib
import logging
import re
import timeago #new addition
from email.mime.text import MIMEText #new addition
from email.mime.multipart import MIMEMultipart # new Addtion
import webbrowser # if not Used Please Remove

app = Flask(__name__)

sslify = SSLify(app)

app.config['TEMPLATES_AUTO_RELOAD'] = True

app.debug = True

app.secret_key = os.urandom(12)

logging.basicConfig(filename='logs.log', level=logging.ERROR)

date = datetime.datetime.now()


'''
                        WRITE FUNCTIONS HERE
'''
# server object creation to send emails


def serve():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    # authentication
    server.login(urhope_mail, urhope_pass)
    return server


def get_db():
    db = pymysql.connect(host=host, user=username, passwd=password,
                         db=db_name, charset='utf8mb4')
    return db



'''
                        WRITE ROUTES HERE
'''
@app.route('/')
def base():
    return render_template('home.html')


@app.route('/relief/', methods=['GET'])
def relief():
    return render_template('relief_pincode_page.html')

@app.route('/food/', methods=['GET','POST'])
def foodbank():
    return render_template('foodbank.html')

@app.route('/relief_call/', methods=['GET'])
def relief_call():
    return render_template('relief_call.html')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if 'username' in request.form \
                and 'password' in request.form and 'role' in request.form \
                and 'confirm' in request.form and 'serve' in request.form:
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')
            confirmpassword = request.form.get('confirm')
            pincode = request.form.get('pincode')
            phone = request.form.get('phone')
            role = request.form.get('role')
            age = request.form.get('age')
            curr = request.form.get("currProfile")
            gender = request.form.get("gender")
            regno = request.form.get('regno')
            branch = request.form.get("branch")
            website = request.form.get("website")
            social = request.form.get("social")
            about = request.form.get("about")
            govtID = request.form.get("govtID")
            address = request.form.get("address")
            service = request.form.getlist("serve")
            print(service)

            services = ''
            for s in service:
                services = services + s + ','

            ph = len(phone)
            if (ph >= 11 or ph <= 9) or (not phone.isdigit()):
                flash("Invalid Phone number. Length of the phone number should be 10.")
                return redirect(url_for('signup'))

            pi = len(pincode)
            if (pi >= 7 or pi <= 5) or (not pincode.isdigit()):
                flash("Invalid pincode. Pincode should be a 6 digit number.")
                return redirect(url_for('signup'))

            try:
                db = get_db()
                c = db.cursor()
                c.execute(
                    'select username from members where username = %s', username)
                account = c.fetchone()

                c.execute('select phone from members where phone = %s', phone)
                p = c.fetchone()

                if account:
                    flash('Email already exists please try again with another email!')
                    return render_template('register.html')
                elif p:
                    flash(
                        'The phone number already exists please try again with another phone number.')
                    return render_template('register.html')
                else:
                    if password == confirmpassword:
                        c.execute('insert into members (name, username, phone, pin, role, services, regno, branch, sex, age, currProfile, website, social, govtID, address, about, password ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, md5(%s))', (
                            name,
                            username,
                            phone,
                            pincode,
                            role,
                            services,
                            regno,
                            branch,
                            gender,
                            age,
                            currProfile,
                            website,
                            social,
                            govtID,
                            address,
                            about,
                            password,
                        ))
                        db.commit()

                        flash(
                            'Registered Successfully, Check your email for confirmation!')

                        server = serve()
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = "Notification from URHope Team"
                        html= render_template('mail/register.html', name=name, username=username, password=password)
                        body = MIMEText(html, 'html')
                        msg.attach(body)
                        server.sendmail(
                                        'urhope.ngo@gmail.com',
                                        str(username),
                                        msg.as_string()
                                        )

                        server.quit()

                        c.close()
                        db.close()

                        return redirect(url_for('login'))

                    else:
                        flash('Passwords do not match!')
                        return render_template('register.html')
            except Exception as e:
                print(e)
                flash("An error occured. Please try again.")
                return render_template('register.html')
        else:
            flash("Please enter all the details.")
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form \
            and 'password' in request.form:
        try:
            username = request.form['username']
            password = request.form['password']

            email_expression = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            if(re.search(email_expression, username)):
                db = get_db()
                c = db.cursor()
                c.execute('SELECT id,name, username, password, role, phone, pin, regno, age, sex, currProfile, address, social, services, branch, about, govtID, website from members WHERE username = %s and password = md5(%s)', (username, password))
                account = c.fetchone()
            else:
                ph = len(username)
                if (ph >= 11 or ph <= 9) or (not username.isdigit()):
                    flash("Invalid Email or Phone number. Please try again.")
                    return redirect(url_for('login'))

                db = get_db()
                c = db.cursor()
                c.execute('SELECT id,name, username, password, role, phone, pin, regno, age, sex, currProfile, address, social, services, branch, about, govtID, website from members WHERE phone = %s and password = md5(%s)', (username, password))
                account = c.fetchone()

            if account is not None:
                session['logged_in'] = True
                session['user_id'] = account[0]
                session['username'] = account[2]
                session['name'] = account[1]
                session['role'] = account[4]
                session['pin'] = account[6]
                session['phone'] = account[5]
                session['regno'] = account[7]
                session['age'] = account[8]
                session['sex'] = account[9]
                session['address'] = account[11]
                session['currProfile'] = account[10]
                session['social'] = account[12]
                session['services'] = account[13]
                session['branch'] = account[14]
                session['about'] = account[15]
                session['govtID'] = account[16]
                session['website'] = account[17]

                active = 1
                c.execute('UPDATE members SET active = %s where username = %s and password = md5(%s)',
                          (active, username, password))

                db.commit()
                c.close()
                db.close()
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials. Please try again.')
                return render_template('login.html')
        except Exception as e:
            print(e)
        flash('An error occured. Please try again.')
        return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/change_password/', methods=['GET', 'POST'])
def change_password():
    if request.method == "POST":
        if 'old_password' in request.form and 'new_password' in request.form and 'confirm' in request.form:
            old_pass = request.form['old_password']
            new_pass = request.form['new_password']
            confirm_new_pass = request.form['confirm']

            username = session['username']
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'SELECT * FROM members WHERE username = %s and password = md5(%s)', (username, old_pass))
            account = cursor.fetchone()
            db.commit()
            cursor.close()
            db.close()

            if account is None:
                flash(
                    "The current password that you have entered is invalid. Please try again.")
                return redirect(url_for('profile', id=session['user_id']))
            elif new_pass != confirm_new_pass:
                flash(
                    "New passwords does not match. Make sure confirm password is same as new password.")
                return redirect(url_for('profile', id=session['user_id']))
            else:
                try:
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute(
                        'UPDATE members SET password = md5(%s) WHERE username = %s', (new_pass, username))
                    flash("Password updated successfully.")
                    db.commit()
                    cursor.close()
                    db.close()
                    return redirect(url_for('logout'))
                except Exception as e:
                    print(e)
        else:
            flash("Please fill all the details.")
            return redirect(url_for('profile', id=session['user_id']))
    else:
        return redirect(url_for('profile', id=session['user_id']))


@app.route('/forgot_password/', methods=['GET', 'POST'])
def forgot_passsword():
    flash("We are working on this part. It will be updated soon.")
    return redirect(url_for('login'))

    # Codes below will be considered after successful implementation of password link generation mechanism
    if request.method == "POST":
        email = request.form['username']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM members WHERE username = %s', (email))
        account = cursor.fetchone()
        db.commit()
        cursor.close()
        db.close()

        if account is None:
            flash("Entered Email ID does not exist in our databse. Please try again. In case of any query you can contact us.")
            return redirect(url_for('forgot_passsword'))
        else:
            x = "We have sent your login details to "+email + \
                ". In case of any query you can contact us."
            flash(x)
            name = account[1]
            # password = account[3] #It's hashed password. There isn't any python function to decrypt it
            password = "none"
            server = serve()
            subject = "Notification from URHope Team"
            body = "Dear "+name+",\n\nYour login details.\n\nUsername: "+email+"\nPassword: "+password + \
                "\n\nClick here to login.\nhttp://urhope.in/login/\n\nThanks for choosing us. Have a nice day :)\n\nRegards\nURHope Team"
            msg = f"Subject: {subject}\n\n{body} "
            server.sendmail(
                'urhope.ngo@gmail.com',
                str(email),
                msg
            )
            server.quit()

            return redirect(url_for('forgot_passsword'))
    else:
        return render_template('forgot_pass.html')


@app.route('/logout')
def logout():
    if session['role'] != 'a':
        id = session['user_id']
        active = 0
        db = get_db()
        c = db.cursor()
        c.execute('UPDATE members SET active = %s where id = %s', (active, id))
        db.commit()
        c.close()
        db.close()

    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/team')
def team():
    return render_template('team.html')


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if session['role'] == 'v':
            account_page=True
            all = allTasks()
            applied = appliedTasks()
            db = get_db()
            c = db.cursor()
            c.execute('SELECT task_id,vol_id FROM application ORDER BY task_id ASC')
            app_data = c.fetchall()
            c.close()
            db.close()
            done=[]
            for i in app_data:
                if i[1]==session['user_id']:
                    done.append(i[0])
            return render_template('volunteers_dashboard.html', all=all, applied=applied, done=done, account_page=account_page)
        if session['role'] == 'n':
            account_page=True
            myTask = myTasks()
            notif=notification()
            l=len(notif)
            return render_template('ngo_dashboard.html', myTask=myTask, notif=notif, account_page=account_page, l=l)
        if session['role'] == 'a':
            account_page=True
            regvols = reg_vols()
            regngos = reg_ngos()
            all = allTasks()
            log = logs()
            return render_template('admin_dashboard.html', account_page=account_page, all=all, regvols=regvols, regngos=regngos, logs=log)

@app.route('/panel/')  # Admin Login
def admin_panel():
    return render_template('adminlogin.html')


@app.route('/check-admin', methods=['GET', 'POST'])
def admin_check():
    if request.method == 'POST' and 'username' in request.form \
            and 'password' in request.form:
        try:
            username = request.form['username']
            password = request.form['password']
            db = get_db()
            c = db.cursor()
            c.execute(
                'SELECT id,name,username,role FROM admin WHERE username = %s and password = md5(%s)', (username, password))
            account = c.fetchone()
            if account is not None:
                session['logged_in'] = True
                session['user_id'] = account[0]
                session['username'] = account[2]
                session['name'] = account[1]
                session['role'] = account[3]
                return redirect(url_for('home'))
            else:
                flash('Invalid Username or Password')
                return redirect(url_for('admin_panel'))
        except Exception as e:
            print(e)
            return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('admin_panel'))


# @app.route('/reg_ngos')
# def reg_ngos():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))
#     db = get_db()
#     c = db.cursor()
#     role = "n"
#     c.execute('SELECT * FROM members WHERE role=%s ORDER BY active DESC', (role))
#     data = c.fetchall()
#     l = len(data)
#     db.commit()
#     c.close()
#     db.close()
#     return render_template('view_ngo.html', data=data, l=len(data))


@app.route('/del_ngo/<id>', methods=['GET', 'POST'])
def del_ngo(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('logout'))
    db = get_db()
    c = db.cursor()

    c.execute('SELECT username FROM members WHERE id = %s', id)
    data = c.fetchone()
    uname = data[0]

    c.execute('DELETE FROM application WHERE grp_email = %s', uname)
    c.execute('DELETE FROM task WHERE grp_email = %s', uname)
    c.execute('DELETE FROM members WHERE id = %s', id)

    db.commit()
    c.close()
    db.close()
    return redirect(url_for('home'))


# @app.route('/reg_vols')
# def reg_vols():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))
#     db = get_db()
#     c = db.cursor()
#     role = "v"
#     c.execute('SELECT * FROM members WHERE role=%s ORDER BY active DESC', (role))
#     data = c.fetchall()
#     l = len(data)
#     db.commit()
#     c.close()
#     db.close()
#     return render_template('view_volun.html', data=data, l=l)


@app.route('/del_vol/<id>')
def del_vol(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    c = db.cursor()

    c.execute('SELECT username FROM members WHERE id = %s', id)
    data = c.fetchone()
    vol_mail = data[0]

    c.execute('SELECT grp_email FROM application WHERE vol_email = %s', vol_mail)
    gdata = c.fetchall()

    if len(gdata) > 0:
        for i in gdata:
            # deletes all the volunteer applications
            c.execute(
                'SELECT vol_applied FROM task WHERE grp_email=%s', (i[0]))
            val = c.fetchone()
            val = val[0]-1
            c.execute(
                'UPDATE task SET vol_applied= %s WHERE grp_email=%s', (val, i[0]))
        c.execute('DELETE FROM application WHERE vol_email = %s', vol_mail)

    c.execute('DELETE FROM members WHERE id = %s', id)
    db.commit()
    c.close()
    db.close()
    return redirect(url_for('home'))


# @app.route('/logs')
# def logs():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))

#     log_file = open('logs.log', 'r')

#     if os.stat("logs.log").st_size == 0:
#         return redirect('home', logs=log_file, l=0)
#     else:
#         return redirect('home', logs=log_file, l=1)


# @app.route('/download_data/<id>/', methods=["GET", "POST"])
# def download_data(id):
#     id = id
#     new = id
#     connect = get_db()
#     cursor = connect.cursor()
#     cursor.execute("SELECT * FROM application WHERE task_id=%s", id)
#     data = cursor.fetchall()

#     if(len(data) > 0):
#         id = data[0][3]
#         # naming = data[0][7]
#         # grp_name = data[0][5]

#         cursor.execute(
#             "SELECT vol_name,vol_email,vol_phone FROM application WHERE task_id=%s", id)
#         data = cursor.fetchall()

#         columns = ['Volunteer Name', 'Volunteer Email', 'Volunteer Contact No']
#         df = pd.DataFrame(list(data), columns=columns)

#         # filename = str(id)+"_Volunteers.xlsx"

#         # try:
#         #     os.remove("templates/downloaded_data/Volunteer.xlsx")
#         # except OSError:
#         #     pass
#         path = "templates/downloaded_data/Volunteer.xlsx"

#         # writer = pd.ExcelWriter(filename,engine = "openpyxl"
#         writer = pd.ExcelWriter(path, engine='xlsxwriter')
#         df.to_excel(writer, sheet_name='Task Volunteer')

#         writer.save()

#         cursor.execute('select * from application where task_id = %s', new)
#         data = cursor.fetchall()

#         connect.commit()
#         cursor.close()
#         connect.close()

#         download = 1
#         # ,download=download,false_id=id,filename=filename

#         return render_template('applied_vols.html', len=len(data), data=data)
#     else:
#         connect.commit()
#         cursor.close()
#         connect.close()
#         flash("You can't download because there aren't any volunteer who has applied for this task")
#         return redirect(url_for('task_list'))


@app.route('/<id>/', methods=['GET', 'POST'])
def profile(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if session['role'] == 'v':
            account_page=True
            return render_template('volunteers_profile.html',
                                   id=session['user_id'], account_page=account_page)
        if session['role'] == 'n':
            account_page=True
            return render_template('ngo_profile.html',
                                   id=session['user_id'], account_page=account_page)
        if session['role'] == 'a':
            account_page=True
            return render_template('admin_profile.html',
                                   id=session['user_id'], account_page=account_page)


@app.route('/edit/<id>/', methods=['GET', 'POST'])
def edit_profile(id):
    if not session.get('logged_in'):
        return redirect(url_for('logout'))
    else:
        if session['role'] == 'v':
            account_page=True
            return render_template('edit_profile_v.html',
                                   id=session['user_id'], account_page=account_page)
        elif session['role'] == 'n':
            account_page=True
            return render_template('edit_profile_n.html',
                                   id=session['user_id'],account_page=account_page)
        else:
            return render_template('home.html')


@app.route('/update', methods=['GET', 'POST'])
def update_pro():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        username = session['username']
        role = session['role']

        if role == 'V' or role == 'v':

            if request.method == 'POST':
                if 'name' in request.form \
                        and 'pin' and request.form and 'phone' in request.form \
                        and 'address' in request.form and 'about' in request.form \
                        and 'serve' in request.form and 'age' in request.form\
                        and 'gender' in request.form and 'currProfile' in request.form:

                    name = request.form.get('name')
                    pincode = request.form.get('pin')
                    phone = request.form.get('phone')
                    address = request.form.get('address')
                    age = request.form.get('age')
                    sex = request.form.get('gender')
                    currProfile = request.form.get('currProfile')
                    about = request.form.get('about')
                    service = request.form.getlist("serve")

                    services = ''
                    for s in service:
                        services = services + s + ','

                    ph = len(phone)
                    if (ph >= 11 or ph <= 9) or (not phone.isdigit()):
                        flash(
                            "Invalid Phone number. Length of the phone number should be 10.")
                        return redirect(url_for('profile', id=session['user_id']))

                    pi = len(pincode)
                    if (pi >= 7 or pi <= 5) or (not pincode.isdigit()):
                        flash("Invalid pincode. Pincode should be a 6 digit number.")
                        return redirect(url_for('profile', id=session['user_id']))

                    connect = get_db()
                    exe = connect.cursor()

                    exe.execute('UPDATE members SET name=%s,pin=%s, phone=%s, services=%s, age=%s, sex=%s, currProfile=%s, address=%s,about=%s WHERE username = %s ', (
                        name,
                        pincode,
                        phone,
                        services,
                        age,
                        sex,
                        currProfile,
                        address,
                        about,
                        username,
                    ))

                    exe.execute(
                        "UPDATE application SET vol_name=%s, vol_phone=%s WHERE vol_email=%s", (name, phone, username))

                    connect.commit()
                    exe.close()
                    connect.close()
                    flash('Profile was updated successfully.')
                    return redirect(url_for('logout'))
                else:
                    flash('Please fill all the details.')
                    return redirect(url_for('profile', id=session['user_id']))
            else:
                flash('Profile was not updated')
                return redirect(url_for('profile', id=session['user_id']))

        elif role == 'n' or role == 'N':
            if request.method == 'POST':
                if 'name' in request.form \
                        and 'serve' in request.form and 'address' \
                        in request.form and 'regno' in request.form \
                        and 'phone' in request.form and 'pin' \
                        in request.form and 'about' in request.form:

                    name = request.form.get('name')
                    website = request.form.get('website')
                    social = request.form.get('social')
                    address = request.form.get('address')
                    regno = request.form.get('regno')
                    branch = request.form.get('branch')
                    phone = request.form.get('phone')
                    pin = request.form.get('pin')
                    about = request.form.get('about')
                    service = request.form.getlist("serve")

                    services = ''
                    for s in service:
                        services = services + s + ','

                    ph = len(phone)
                    if (ph >= 11 or ph <= 9) or (not phone.isdigit()):
                        flash(
                            "Invalid Phone number. Length of the phone number should be 10.")
                        return redirect(url_for('profile', id=session['user_id']))

                    pi = len(pin)
                    if (pi >= 7 or pi <= 5) or (not pin.isdigit()):
                        flash("Invalid pincode. Pincode should be a 6 digit number.")
                        return redirect(url_for('profile', id=session['user_id']))

                    connect = get_db()
                    exe = connect.cursor()

                    exe.execute('UPDATE members SET name=%s,website=%s, social=%s,services=%s,address=%s,regno=%s,branch=%s,phone=%s,pin=%s,about=%s WHERE username = %s ', (
                        name,
                        website,
                        social,
                        services,
                        address,
                        regno,
                        branch,
                        phone,
                        pin,
                        about,
                        username,
                    ))

                    exe.execute("UPDATE task SET grp=%s, website = %s, phone=%s, abt_grp=%s, location=%s WHERE grp_email=%s", (
                        name, website, phone, about, pin, username))
                    exe.execute(
                        "UPDATE application SET grp_name=%s WHERE grp_email=%s", (name, username))

                    connect.commit()
                    exe.close()
                    connect.close()

                    flash('Profile was updated successfully.')
                    return redirect(url_for('logout'))
                else:
                    flash("Please fill all the details.")
                    return redirect(url_for('profile', id=session['user_id']))
            else:
                flash('Profile was not updated')
                return redirect(url_for('profile', id=session['user_id']))
        else:
            flash("Sorry! You can't update.")
            return redirect(url_for('logout'))


@app.route('/create-task', methods=['GET', 'POST'])
def create_task():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    elif session['role'] == 'n':
        account_page=True
        myTask = myTasks()
        if request.method == 'POST':
            task = request.form['task']
            grp = request.form.get('grp', session['name'])
            website = request.form['website']
            phone = request.form['phone']
            vol_num = request.form['vol_num']
            pincode = request.form['pin']
            task_det = request.form['task_det']
            t_type = request.form['t_type']
            email = session['username']
            about = session['about']
            connect = get_db()
            exe = connect.cursor()
            exe.execute('insert into task (task, grp, website, location, phone, vol_num, task_det, t_type, abt_grp, grp_email) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                task,
                grp,
                website,
                pincode,
                phone,
                vol_num,
                task_det,
                t_type,
                about,
                email,
            ))
            connect.commit()
            exe.close()
            connect.close()
            flash('Task has been added successfully.')
            return render_template('create_task.html', account_page=account_page, myTask = myTask)
        else:
            return render_template('create_task.html', account_page=account_page, myTask = myTask)
    else:
        flash("Task was not added. Try again")
        return render_template('create_task.html', account_page=account_page, myTask = myTask)


@app.route('/edit-task/<id>/', methods=['GET', 'POST'])
def edit_task(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    elif session['role'] == 'n':
        account_page=True
        myTask=myTasks()
        if request.method == 'POST':
            task = request.form['task']
            grp = request.form['grp']
            website = request.form['website']
            phone = request.form['phone']
            vol_num = request.form['vol_num']
            pincode = request.form['pin']
            task_det = request.form['task_det']
            t_type = request.form['t_type']

            connect = get_db()
            exe = connect.cursor()

            exe.execute('UPDATE task SET task=%s, grp=%s, website=%s, location=%s, phone=%s, vol_num=%s, task_det=%s, t_type=%s where id= %s', (
                task,
                grp,
                website,
                pincode,
                phone,
                vol_num,
                task_det,
                t_type,
                id,

            ))

            exe.execute(
                'UPDATE application SET task_name=%s WHERE task_id = %s', (task, id))

            connect.commit()
            exe.close()
            connect.close()
            flash('Task has been updated')
            return redirect(url_for('home'))
        else:
            db = get_db()
            c = db.cursor()
            c.execute('SELECT * FROM task WHERE id = %s', id)
            data = c.fetchall()
            db.commit()
            c.close()
            db.close()
            return render_template('edit_task.html', data=data, account_page=account_page, myTask=myTask)
    else:
        return redirect(url_for('home'))


@app.route('/delete-task/<id>/')
def delete_task(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    elif session['role'] == 'n':
        db = get_db()
        c = db.cursor()
        c.execute('DELETE FROM task WHERE id = %s', id)
        c.execute('SELECT * FROM application WHERE task_id = %s', id)
        data = c.fetchall()

        if len(data) != 0:
            c.execute('DELETE FROM application WHERE task_id = %s', id)

        db.commit()
        c.close()
        db.close()

        x = "Task with ID " + \
            str(id)+" has been deleted successfully. If you had any volunteer applied for this task their application has also been deleted."
        flash(x)

        return redirect(url_for('home'))
    else:
        flash("Task was not deleted")
        return redirect(url_for('home'))


# @app.route('/task_list')
# def task_list():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))

#     elif session['role'] == 'n':
#         grp_name = session['name']
#         db = get_db()
#         c = db.cursor()
#         c.execute('select * from task where grp = %s', grp_name)
#         data = c.fetchall()
#         db.commit()
#         c.close()
#         db.close()
#         return render_template('task_list_n.html', len=len(data), data=data, download=0, false_id=-1)

#     elif session['role'] == 'a':
#         grp_name = session['name']
#         db = get_db()
#         c = db.cursor()
#         c.execute('select * from task')
#         data = c.fetchall()
#         db.commit()
#         c.close()
#         db.close()
#         return render_template('task_list.html', len=len(data), data=data)

#     elif session['role'] == 'v':
#         db = get_db()
#         c = db.cursor()
#         c.execute('SELECT * FROM task ORDER BY location ASC')
#         data = c.fetchall()

#         c.execute('SELECT task_id,vol_id FROM application ORDER BY task_id ASC')
#         app_data = c.fetchall()

#         id = session['user_id']

#         db.commit()
#         c.close()
#         db.close()

#         applied = []
#         for i in app_data:
#             if i[1] == session['user_id']:
#                 applied.append(i[0])
#         return render_template('task_list_v.html', id=id, l=len(app_data), applied=applied, len=len(data), data=data, app_data=app_data)
#     else:
#         return redirect(url_for('login'))


@app.route('/apply/<id>/', methods=['GET', 'POST'])
def apply_task(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    c = db.cursor()
    server = serve()

    c.execute('SELECT * FROM application WHERE vol_email=%s',
              session['username'])
    data = c.fetchall()

    if len(data) >= 2:
        db.commit()
        c.close()
        db.close()
        flash("You can't apply for this task. You can volunteer maxmimum for 2 tasks at a time."
              )
        return redirect(url_for('home'))

    c.execute('SELECT * FROM task where id=%s', id)
    data = c.fetchall()

    vol_req = data[0][7]
    grp_name = data[0][3]
    task_name = data[0][1]
    task_id = data[0][0]
    if data[0][11] < data[0][7]:
        val = data[0][11]+1
        c.execute('UPDATE task SET vol_applied=%s WHERE id=%s', (val, id))
        c.execute('INSERT INTO application(grp_email,vol_email,task_id,vol_id,grp_name,vol_name,task_name,vol_phone) values(%s,%s,%s,%s,%s,%s,%s,%s)',
                  (data[0][12], session['username'], data[0][0], session['user_id'], data[0][3], session['name'], data[0][1], session['phone']))
        db.commit()
        c.close()
        db.close()

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Notification from URHope Team"
        html= render_template('mail/task_apply.html', grp_name=grp_name, task_name=task_name,  task_id=task_id, val=val, vol_req=vol_req)
        body = MIMEText(html, 'html')
        msg.attach(body)

        server.sendmail(
						'urhope.ngo@gmail.com',
						str(data[0][12]),
						msg.as_string()
						)

        if(val == data[0][7]):
            html= render_template('mail/task_sufficient.html', grp_name=grp_name, task_name=task_name,  task_id=task_id, val=val, vol_req=vol_req)
            body = MIMEText(html, 'html')
            msg.attach(body)
            server.sendmail(
							'urhope.ngo@gmail.com', 
							str(data[0][12]), 
							msg.as_string()
							)
        server.quit()
        flash("Applied Successfully")
        return redirect(url_for('home'))
    else:
        db.commit()
        c.close()
        db.close()
        x = "Thank You " + \
            session['name']+"!\nThere are sufficient volunteers available for this task. Try applying for some other task."
        flash(x)
        return redirect(url_for('home'))


@app.route('/back_application/<id>/', methods=['GET', 'POST'])
def back_application(id):
    id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    c = db.cursor()

    c.execute('DELETE FROM application WHERE vol_email=%s and task_id=%s',
              (session['username'], id))
    c.execute('SELECT * FROM task WHERE id=%s', id)
    data = c.fetchall()
    val = data[0][11]
    task_name = data[0][1]
    task_id = data[0][0]
    vol_req = data[0][7]
    grp_name = data[0][3]

    val = val - 1
    c.execute('UPDATE task SET vol_applied=%s WHERE id=%s', (val, id))

    server = serve()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Notification from URHope Team"
    html= render_template('mail/back_application.html', grp_name=grp_name, val=val, task_name=task_name, task_id=task_id, vol_req=vol_req)
    body = MIMEText(html, 'html')
    msg.attach(body)

    server.sendmail(
                    'urhope.ngo@gmail.com_address',
                    str(data[0][12]),
                    msg.as_string()
                    )

    db.commit()
    c.close()
    db.close()
    server.quit()
    flash("Changes applied successfully.")
    return redirect(url_for('home'))


@app.route('/applied_vols/<id>', methods=['GET', 'POST'])
def applied_vols(id):
    task_id = id
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    c = db.cursor()
    c.execute(
        'SELECT * FROM application WHERE task_id=%s ORDER BY vol_name', task_id)
    data = c.fetchall()
    db.commit()
    c.close()
    db.close()
    return render_template('applied_vols.html', len=len(data), data=data)


# @app.route('/whatsapp/<id>', methods=['GET', 'POST'])
# def whatsapp(id):
#     id = id
#     db = get_db()
#     c = db.cursor()
#     c.execute('select task_name,vol_name,vol_phone,task_id from application where id = %s and grp_email = %s',
#               (id, session['username']))
#     task = c.fetchone()

#     task_name = task[0]
#     name = task[1]
#     phone = task[2]
#     task_id = task[3]

#     r = request.headers.get('User-Agent')
#     dev = SoftwareDetector(r).parse()
#     opsys = dev.os_name()

#     MobOS = ['Android', 'iOS', 'BlackBerry OS', 'BlackBerry 10', 'BlackBerry PlayBook OS',
#              'Windows Phone', 'Windows RT', 'Windows Mobile', 'Bada', 'Symbian OS', 'Aliyun OS',
#              'Firefox OS', 'Ubuntu Touch', 'Nokia Asha', 'Palm OS', 'Series 40', 'Sailfish OS',
#              'GridOS', 'Mer project', 'Brew', 'SHR', 'Web OS', 'Tizen', 'Dnager OS', 'Limo 4',
#              'Maemo', 'MeeGo', 'KaiOS', 'Nucleus RTOS', 'PostMarketOS', 'HarmonyOS']

#     if opsys in MobOS:
#         x = "https://api.whatsapp.com/send?phone=+91"+phone+"&text=Dear%20"+name+"%2C%0D%0A%0D%0AWe%20are%20glad%20that%20you%20have%20opted%20to%20volunteer%20for%20the%20task:%20" + \
#             task_name+",%20created%20by%20us.%0D%0A%0D%0AThank you so much.%0D%0A%0D%0AFor%20any%20queries%20you%20can%20contact%20us.%0D%0A%0D%0ARegards,%0D%0A" + \
#             session['name']
#         webbrowser.open(x, 0)
#         flash("Message Sent")
#         return redirect(url_for('applied_vols', id=task_id))
#     else:
#         x = "https://web.whatsapp.com/send?phone=+91"+phone+"&text=Dear%20"+name+"%2C%0D%0A%0D%0AWe%20are%20glad%20that%20you%20have%20opted%20to%20volunteer%20for%20the%20task:%20" + \
#             task_name+",%20created%20by%20us.%0D%0A%0D%0AThank you so much.%0D%0A%0D%0AFor%20any%20queries%20you%20can%20contact%20us.%0D%0A%0D%0ARegards,%0D%0A" + \
#             session['name']
#         webbrowser.open(x, 0)
#         flash("Message Sent")
#         return redirect(url_for('applied_vols', id=task_id))

#     flash("An Error occured or you are on an invalid URL. Can't send the message.")
#     return redirect(url_for('applied_vols', id=task_id))


# @app.route('/notification_page/', methods=['GET', 'POST'])
# def notification_page():
#     if not session.get('logged_in'):
#         return redirect(url_for('logout'))
#     db = get_db()
#     c = db.cursor()
#     c.execute('SELECT * FROM application WHERE grp_email=%s ORDER BY id DESC',
#               session['username'])
#     data = c.fetchall()
#     db.commit()
#     c.close()
#     db.close()
#     return render_template('notification_page.html', len=len(data), data=data)


@app.route('/how_is_the_task/<id>/', methods=['GET', 'POST'])
def how_is_the_task(id):
    if not session.get('logged_in'):
        return redirect(url_for('logout'))

    id = id
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM task WHERE id=%s', id)
    data = c.fetchall()
    db.commit()
    c.close()
    db.close()

    x = "Hey "+session['name']+",for the task '"+data[0][1]+"', total number of applications are " + \
        str(data[0][11])+". You need "+str(data[0][7] -
                                           data[0][11])+" more volunteer to start the task."
    flash(x)
    return redirect(url_for('home'))


@app.route('/find_ngo/', methods=['GET'])
def find_ngo():
    connect = get_db()
    pincode = request.args.get("pincode")
    type = " ".join(request.args.get("service").split("_"))
    pincode = int(pincode)
    c = connect.cursor()
    counter = 0
    where = ""
    for i in [0, -1, +1, -2, +2, -3, +3, -4, +4]:
        where += "m.pin='"+str(pincode+i) + "' OR "
    query = "select distinct m.pin, phone, services, statename, about,website,address, name, username from members m join podata p on m.pin = p.pin where m.role='n' AND (" + where[
        :-4] + ")"
    c.execute(query)
    data = c.fetchall()
    ndata = {'data': []}
    if data:
        for val in data:
            if type in val[2].split(","):
                ndata['data'].append({
                    "pin": val[0],
                    "phone": [val[1]],
                    "services": val[2],
                    "statename": val[3],
                    "about": val[4],
                    "website": val[5],
                    "address": val[6],
                    "name": val[7],
                    "email": val[8]
                })
        c.close()
        connect.close()
        return render_template('ngo_initiatives.html', ndata=ndata, type=type, pin=pincode, data={})
    return render_template('ngo_initiatives.html', type=type, pin=pincode, ndata={})


@app.route('/find_relief/', methods=['GET'])
def find_relief():
    pincode = request.args.get("pincode")
    if pincode and re.fullmatch("[1-9][0-9]{5}", pincode):
        connect = get_db()
        c = connect.cursor()
        query = "select distinct p.statename, p.districtname, s.districthelpline, s.statehelpline, s.created_on from statewisehelplinenos s join podata p on s.districtname = p.districtname where pin='%s'" % pincode
        c.execute(query)
        data = c.fetchone()
        if not data:
            query = "select distinct p.statename, p.districtname, s.districthelpline, s.statehelpline, s.created_on from statewisehelplinenos s join podata p on s.statename = p.statename where pin='%s'" % pincode
            c.execute(query)
            data = c.fetchone()
        if not data:
            query = "select distinct statename from podata where pin='%s'" % pincode
            c.execute(query)
            data = c.fetchone()
        if data:
            c.close()
            connect.close()
            return render_template('find_relief.html', data=data, pin=str(pincode))
    return render_template('find_relief.html', data={}, pin=str(pincode))


@app.route('/initiatives/', methods=['GET'])
def initiatives():
    pincode = request.args.get("pincode")
    pdata = {'data': []}
    dropdown = set()
    type = " ".join(request.args.get("type").split("_"))
    if pincode and re.fullmatch("[1-9][0-9]{5}", pincode):
        connect = get_db()
        pincode = int(pincode)
        c = connect.cursor()
        counter = 0
        data = []
        where = ""
        for i in [0, -1, +1, -2, +2, -3, +3, -4, +4]:
            where += "p.pin='"+str(pincode+i) + "' OR "
        query = "select distinct g.statename, g.districtname, title, description, helplinenumbers, link, eligibility, documents, duration, created_on, dropdown, g.id, g.sourcelink, g.relevantinfo from govtdata g join podata p on g.districtname = p.districtname where (" + where[
            :-4] + ")" + " AND type='" + type + "'"
        c.execute(query)
        data = c.fetchall()

        query = "select distinct g.statename, g.districtname, title, description, helplinenumbers, link, eligibility, documents, duration, created_on, dropdown, g.id, g.sourcelink, g.relevantinfo from govtdata g join podata p on g.statename = p.statename where (" + where[
            :-4] + ")" + " AND type='" + type + "' AND g.districtname='ALL';"
        c.execute(query)
        state_data = c.fetchall()
        full_data = data + state_data
        for d in full_data:
            if d:
                pdata['data'].append({
                    "statename": d[0],
                    "districtname": d[1],
                    "title": d[2],
                    "description": d[3],
                    "helplinenumbers": d[4].split(";") if d[4] else [],
                    "links": d[5],
                    "eligibility": d[6],
                    "documents": d[7],
                    "duration": d[8],
                    "created_on": d[9],
                    "dropdown": d[10],
                    "id": d[11],
                    "sourcelink": d[12].replace("\n", "") if d[12] else "",
                    "relevantinfo": d[13]
                })
                dropdown.add(d[10])
        c.close()
        connect.close()
    return render_template('list_of_initiatives.html', data=pdata, type=type, pin=pincode, dropdown=list(dropdown))


# @app.route('/searchresult',methods=['GET','POST'])
# def serch_result():
#     if request.method=="POST":
#         name = request.form['name']
#         pin = request.form['pin']
#         lpin=len(pin)
#         low_name = name.lower()
#         role='n'

#         if lpin==6:
#             pin = int(pin)
#             pin=pin
#             db = get_db()
#             c = db.cursor()
#             c.execute('SELECT * FROM members WHERE services=%s and pin=%s and role=%s ORDER BY pin ASC',(name,pin,role))
#             data = c.fetchall()
#             l=len(data)
#             db.commit()
#             c.close()
#             db.close()
#             if(l>0):
#                 return render_template('searched.html',l=l,data=data,name=low_name)
#             else:
#                 return render_template('searched.html',l=0)
#         else:
#                 return render_template('searched.html',l=0)


@app.route('/relief_send', methods=['GET', 'POST'])
def relief_send():
    if request.method == "POST" and 'name' in request.form and 'for_appl' in request.form and 'help_type' in request.form and 'govtID' in request.form and 'address' in request.form and 'phone' in request.form and 'pin' in request.form and 'msg' in request.form:
        name = request.form['name']
        for_appl = request.form['for_appl']
        h_type = request.form['help_type']
        govtID = request.form['govtID']
        address = request.form['address']
        phone = request.form['phone']
        pin = request.form['pin']
        msg = request.form['msg']
        role = 'n'
        db = get_db()
        c = db.cursor()

        c.execute(
            'select name,username from members where role = %s and pin=%s and services=%s', (role, pin, h_type))
        account = c.fetchall()

        if len(account) > 0:
            for i in account:
                server = serve()
                subject = "URHope: Hey "+i[0]+"," + \
                    name+" needs some help from you."
                body = "Hello,\n\nThis is a notification from URHope Team. We request you to look into matter as soon as possible and help this needy person.\n\n"+name+" needs help for "+h_type + \
                    " for "+for_appl+".\nContact No: "+phone+"\nAddress: "+address+"\nPincode: "+pin + \
                    "\nGovernment ID: "+govtID+"\n\n"+name + \
                    ", has a message for you,\n"+msg+"\n\nRegards,\nURHope Team"
                msg = f"Subject: {subject}\n\n{body} "

                server.sendmail(
                    'urhope.ngo@gmail.com',  # email ID of URHope or use your email ID for testing
                    str(i[1]),
                    msg
                )
                server.quit()
            flash("Your message has been sent to nearby NGOs. You will receive help.")
            return redirect(url_for('relief_call'))
        else:
            server = serve()
            subject = "URHope Messenger : "+name+" needs some help from you."
            body = "Hello,\n\nWe request you to look into matter as soon as possible and help this needy person.\n\n"+name+" needs help for "+h_type+" for "+for_appl+".\nContact No: " + \
                phone+"\nAddress: "+address+"\nPincode: "+pin+"\nGovernment ID: "+govtID + \
                "\n\nAlso, "+name+" has a message for you,\n" + \
                msg+"\n\nRegards,\nURHope Messenger"
            msg = f"Subject: {subject}\n\n{body} "

            server.sendmail(
                'urhope.ngo@gmail.com',  # email ID of URHope or use your email ID for testing
                'urhope.ngo@gmail.com',
                msg
            )
            server.quit()
            flash("We could not find any NGO nearby you. An email is sent to URHope team. You will get required help soon.")
            return redirect(url_for('relief_call'))
    else:
        flash("Fill all the details before sending.")
        return redirect(url_for('relief_call'))


'''
                        Functions
'''
# new functions added here

def allTasks():
    mydata = {'data': []}
    data = []
    connect = get_db()
    c = connect.cursor()
    query = "select * from task ORDER BY location ASC"
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "task_id": d[0],
                "task": d[1],
                "posted": timeago.format(d[2], date),
                "grp": d[3],
                "website": d[4],
                "location": d[5],
                "phone": d[6],
                "vol_num": d[7],
                "task_det": d[8],
                "t_type": d[9],
                "abt_grp": d[10],
                "vol_applied": d[11],
                "grp_email": d[12]
            })
    c.close()
    connect.close()
    return mydata


def myTasks():
    mydata = {'data': []}
    data = []
    user = session['username']
    connect = get_db()
    c = connect.cursor()
    query = "select * from task where grp_email='%s'" % user
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "task_id": d[0],
                "task": d[1],
                "posted": timeago.format(d[2], date),
                "grp": d[3],
                "website": d[4],
                "location": d[5],
                "phone": d[6],
                "vol_num": d[7],
                "task_det": d[8],
                "t_type": d[9],
                "abt_grp": d[10],
                "vol_applied": d[11],
                "grp_email": d[12]
            })
    c.close()
    connect.close()
    return mydata


def appliedTasks():
    mydata = {'data': []}
    data = []
    id = session['user_id']
    connect = get_db()
    c = connect.cursor()
    query = "select t.id, t.task, t.posted, t.grp, t.website, t.location, t.phone, t.vol_num, t.task_det, t.t_type, t.abt_grp, t.vol_applied, t.grp_email from task t join application a on t.id = a.task_id where vol_id=%s" % id
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "task_id": d[0],
                "task": d[1],
                "posted": timeago.format(d[2], date),
                "grp": d[3],
                "website": d[4],
                "location": d[5],
                "phone": d[6],
                "vol_num": d[7],
                "task_det": d[8],
                "t_type": d[9],
                "abt_grp": d[10],
                "vol_applied": d[11],
                "grp_email": d[12]
            })
    c.close()
    connect.close()
    return mydata


def notification():
    mydata = {'data': []}
    data = []
    user = session['username']
    connect = get_db()
    c = connect.cursor()
    query = "SELECT * FROM application WHERE grp_email='%s' ORDER BY id DESC" % user
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "id": d[0],
                "grp_email": d[1],
                "vol_email": d[2],
                "task_id": d[3],
                "vol_id": d[4],
                "grp_name": d[5],
                "vol_name": d[6],
                "task_name": d[7],
                "vol_phone": d[8],
                "created_at": timeago.format(d[9], date)
            })
    c.close()
    connect.close()
    return mydata

# admin data

def reg_vols():
    mydata = {'data': []}
    data = []
    role = 'v'
    connect = get_db()
    c = connect.cursor()
    query = "SELECT * FROM members WHERE role='%s' ORDER BY active DESC" % role
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "member_id": d[0],
                "name": d[1],
                "username": d[2],
                "password": d[3],
                "regno": d[4],
                "phone": d[5],
                "pin": d[6],
                "role": d[7],
                "website": d[8],
                "age": d[9],
                "sex": d[10],
                "currProfile": d[11],
                "address": d[12],
                "social": d[13],
                "services": d[14],
                "branch": d[15],
                "about": d[16],
                "govtid": d[17],
                "active": d[18],
                "created_on": timeago.format(d[19], date)
            })
    c.close()
    connect.close()
    return mydata


def reg_ngos():
    mydata = {'data': []}
    data = []
    role = 'n'
    connect = get_db()
    c = connect.cursor()
    query = "SELECT * FROM members WHERE role='%s' ORDER BY active DESC" % role
    c.execute(query)
    data = c.fetchall()
    for d in data:
        if d:
            mydata['data'].append({
                "member_id": d[0],
                "name": d[1],
                "username": d[2],
                "password": d[3],
                "regno": d[4],
                "phone": d[5],
                "pin": d[6],
                "role": d[7],
                "website": d[8],
                "age": d[9],
                "sex": d[10],
                "currProfile": d[11],
                "address": d[12],
                "social": d[13],
                "services": d[14],
                "branch": d[15],
                "about": d[16],
                "govtid": d[17],
                "active": d[18],
                "created_on": timeago.format(d[19], date)
            })
    c.close()
    connect.close()
    return mydata

def logs():
    log_file = open('logs.log', 'r')
    log_read = log_file.readlines()
    return log_read

#mail Template Admin
@app.route('/admin-mail/', methods=['GET','POST'])
def mail_template():
    if not 'logged_in' in session:
        return redirect(url_for('logout'))
    if session['role'] == 'a':
        account_page=True
        if request.method == 'POST':
            if 'email' in request.form:
                email = request.form.get('email')
                subject = request.form.get('subject')
                message = request.form.get('message')
                server = serve()
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                html= render_template('mail/admin_mail.html', message=message)
                body = MIMEText(html, 'html')
                msg.attach(body)
                server.sendmail(
                                        'urhope.ngo@gmail.com',
                                        str(email),
                                        msg.as_string()
                                        )

                server.quit()
                flash('Email Sent!')
                return render_template('admin_mailer.html', account_page=account_page)
            else:
                flash('Email Not Sent!')
                return render_template('admin_mailer.html', account_page=account_page)
        return render_template('admin_mailer.html', account_page=account_page)


'''
                        ERROR HANDLING
'''
@app.errorhandler(403)
def access_forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500



'''
                        APP RUNNER
'''
if __name__ == '__main__':
    app.run()  # host='0.0.0.0', port=5000

