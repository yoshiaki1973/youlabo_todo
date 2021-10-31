from flask           import *
from flask_paginate  import *
import mysql.connector as mydb
from datetime        import datetime
from email.mime.text import MIMEText
from email.utils     import formatdate
import smtplib
import secrets
import string
import tweepy
import requests
import json
import os

#===================================================
# AWS RDB 設定 (MySQL)
#===================================================

test_mode                       = True

sql_table_user_master           = "todo.user_master"
sql_server                      = "youlabo-mysql.cm185bqkijjo.ap-northeast-1.rds.amazonaws.com"
conn                            = mydb.connect(host=sql_server,port='3306',user='admin',password='forstart#12345',database='todo')

table_user_master               = "user_master"
table_todo_master               = "todo_master"
table_single_todo_master        = "single_todo_master"

table_todo                      = "todo"
table_single_todo               = "single_todo"

view_todo                       = "v_todo"
view_single_todo                = "v_single_todo"

view_todo_master_list           = "v_todo_master_list"        
view_single_todo_master_list    = "v_single_todo_master_list"
view_user_master_list           = "v_user_master_list"   

#===================================================
# Twitter API 認証設定
#===================================================

# @cleaning_lover
API_key                         = 'tvy3oyXU5kdIkZFJr6Fjqvycr'
API_key_secret                  = 'Y2pO7ilI7cP4iX4DBhgsrQIYtyzXbPWlbLruMg9cADibJy9LQd'
Access_token                    = '1224890318547341312-rGTLhp8zaCazalNklkA1G8nFt1jJDR'
Access_token_secret             = 'KvIPPMK5Sfn5fnbmcNH7QblnWaiFao43ldNjhe8IhA4HX'

#===================================================
# 関数（現在時刻を取得）
#===================================================

def get_now():
    dt                          = datetime.now().strftime('%Y-%m-%d')
    return dt

#===================================================
# 関数（メール送信）
#===================================================

def send_email( to_email , subject , body ):
    from_email                  = "kigyoka.com.todo@gmail.com"
    from_name                   = "ユーラボ"
    password                    = "forstart12345"
    smtp_server                 = "smtp.gmail.com"
    port                        = 587
    flag                        = True
    smtp_obj                    = smtplib.SMTP(smtp_server , port)
    smtp_obj.ehlo()
    smtp_obj.starttls()
    smtp_obj.ehlo()
    smtp_obj.login(from_email, password)
    msg                         = MIMEText(body)
    msg['Subject']              = subject
    msg['From']                 = from_name
    msg['To']                   = to_email
    msg['Date']                 = formatdate()
    try:
        smtp_obj.sendmail(from_email, to_email, msg.as_string())    
    except:
        flag                    = False
    smtp_obj.close()
    return flag

def send_mail_new_user( name , email , role , password , twitter ):
    subject                     = "【ユーラボ（ToDo管理システム）】ユーザー登録完了通知"
    msg                         = name + "　様\n\n"
    msg                         = msg + "ユーザー登録しました。\n\n"
    msg                         = msg + "名前："                + name        + "\n"
    msg                         = msg + "メールアドレス："      + email       + "\n"
    msg                         = msg + "Twitter："             + twitter     + "\n"
    msg                         = msg + "ロール："              + role        + "\n"
    msg                         = msg + "初期パスワード："      + password    + "\n\n"
    msg                         = msg + "カリキュラムは、ToDo『A1』よりスタートしてください！\n\n"
    msg                         = msg + "http://13.231.70.201/\n\n"
    res                         = send_email( email , subject , msg )
    return                      res

def send_mail_first_todo( name , email ):
    subject                     = "【ユーラボ（ToDo管理システム）】ToDo カリキュラムを開始してください"
    msg                         = name + "　様\n\n"
    msg                         = msg + "ToDo『A1』よりカリキュラムをスタートしましょう。\n\n"
    msg                         = msg + "ToDoが完了したら「完了」ボタンをクリックしてください。\n\n"
    msg                         = msg + "http://13.231.70.201/\n\n"
    res                         = send_email( email , subject , msg )
    return                      res

def send_mail_password_reissue( email , new_password ):
    subject                     = "【ユーラボ（ToDo管理システム）】パスワードを再発行しました"
    msg                         = "パスワードを再発行しました。\n\n"
    msg                         = msg + "パスワード：" +  new_password + "\n\n"
    msg                         = msg + "http://13.231.70.201/"
    res                         = send_email( email , subject , msg )
    return                      res

#===================================================
# 関数（SQLコマンド実行）
#===================================================

def get_connection():
    sql_server                  = "youlabo-mysql.cm185bqkijjo.ap-northeast-1.rds.amazonaws.com"
    conn                        = mydb.connect(host=sql_server , port='3306' , user='admin', password='forstart#12345', database='todo')
    return conn

def execute(sql):
    flag                        = True
    conn                        = get_connection()
    c                           = conn.cursor()
    try:
        c.execute(sql)
    except:
        flag                    = False
        print(sql,flag)
    conn.commit()
    conn.close()
    return flag

#===================================================
# 関数（ログイン認証）
#===================================================

def login_check(email , password):
    conn                        = get_connection()
    c                           = conn.cursor()
    res                         = "アカウントエラー（登録情報なし）"
    sql                         = "select name from {0} where email = '{1}';".format(table_user_master, email)
    c.execute(sql)
    rows                        = c.fetchall()
    for row in rows:
        name                    = row[0]
        res                     = "パスワードエラー（不一致）"
    sql                         = "select name from {0} where email = '{1}' and password = '{2}';".format(table_user_master, email, password)
    print(sql)
    c.execute(sql)
    rows                        = c.fetchall()
    res                         = False
    for data in rows:
        name                    = data[0]
        res                     = True
        res                     = "ログイン成功"
    conn.commit()
    conn.close()
    return                      res

#===================================================
# パスワード生成／変更
#===================================================

def get_random_password():
    pwd                         = ''.join([secrets.choice(string.ascii_letters + string.digits) for i in range(8)])
    return pwd

def change_password(email,old_password,new_password):
    res                         = login_check( email , old_password )
    if ( res == "ログイン成功" ):
        sql                     = "update {0} set password='{1}' where email='{2}' ;".format(table_user_master, new_password,email)
        flag                    = execute(sql)
    else:
        flag                    = False
    return                      flag
    
#===================================================
# ユーザー情報を取得
#===================================================

# ユーザー情報を取得（メールアドレスから）
def get_user_master_by_email(email):
    conn                    = get_connection()
    c                       = conn.cursor()
    sql                     = "select email, password, name, role, twitter, followers, id from {0} where email = '{1}' ; ".format(table_user_master, email)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        a                   = {'email':data[0] ,'password':data[1] ,'name':data[2],'role':data[3], 'twitter':data[4], 'followers':data[5], 'id':data[6] }
    conn.commit()
    conn.close()
    return                  a

# MySQL
def create_user_master(email,name,role,password,twitter):
    try:
        sql                 = "insert into {0} (email,password,name,role,twitter) values ('{1}','{2}','{3}','{4}','{5}')".format( sql_table_user_master , email , password , name , role , twitter ) 
        flag                = execute(sql)
        if (flag == True):
            send_mail_new_user( name , email , role , password , twitter )
            flag            = True
    except:
        flag                = False
    return flag

# ユーザー設定 削除
def delete_user_master_by_email(email):
    sql                     = "delete from {0} where email='{1}'".format(sql_table_user_master,email)
    return execute(sql)

def email_check(email):
    conn                    = get_connection()
    c                       = conn.cursor()
    flag                    = False
    sql                     = "select email from {0} where email='{1}';".format(sql_table_user_master,email)
    c.execute(sql)
    rows                    = c.fetchall()
    try:
        for data in rows:
            email           = data[0]
            flag            = True
    except:
            flag            = False
    return flag

#===================================================
# ToDo マスタ
#===================================================

# ToDo内容を取得
def get_todo_master_next_todo_id(todo_id):
    a                       = get_todo_master(todo_id)
    return                  a['next_todo_id']

# ToDo マスタ（通常）を取得 
def get_todo_master(todo_id):
    conn                    = get_connection()
    c                       = conn.cursor()
    a                       = {'todo_id':"", 'next_todo_id':"", 'todo':"" }
    sql                     = "select todo_id, next_todo_id, todo , todo_details from {0} where todo_id = '{1}' ; ".format(table_todo_master, todo_id)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        todo_id             = data[0]
        next_todo_id        = data[1]
        todo                = data[2]
        todo_details        = data[3] 
        todo_details        = todo_details.replace("$","'")
        todo_details        = todo_details.replace('#','"')
        a                   = {'todo_id':todo_id, 'next_todo_id':next_todo_id, 'todo':todo, 'todo_details':todo_details}
    conn.commit()
    conn.close()
    return a

# ToDo マスタ（臨時）を取得
def get_single_todo_master(todo_id):
    conn                    = get_connection()
    c                       = conn.cursor()
    sql                     = "select todo_id, todo, exp_date, todo_details from {0} where todo_id='{1}' ; ".format(table_single_todo_master, todo_id)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        todo_id             = data[0]
        todo                = data[1]
        exp_date            = data[2]
        todo_details        = data[3] 
        todo_details        = todo_details.replace("$","'")
        todo_details        = todo_details.replace('#','"')
        a                   = {'todo_id':todo_id , 'todo':todo, 'exp_date':exp_date, 'todo_details':todo_details}
    conn.commit()
    conn.close()
    return a

# ToDo マスタ（通常）の「ToDo ID」を取得
def get_todo_master_todo_ids():
    conn                    = get_connection()
    c                       = conn.cursor()
    a                       = []
    sql                     = "select todo_id from {0};".format(table_todo_master)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        a.append(data[0])
    conn.commit()
    conn.close()
    return a

# ToDo マスタ（通常）の「ToDo ID」を取得
def get_single_todo_master_todo_ids():
    conn                    = get_connection()
    c                       = conn.cursor()
    a                       = []
    sql                     = "select todo_id from {0};".format(table_single_todo_master)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        a.append(data[0])
    conn.commit()
    conn.close()
    return a

#===================================================
# ToDo （通常）
#===================================================

# 新規作成
def create_todo(todo_id, role, mentee, status, start, end, comment):
    print("create_todo")
    flag                    = True
    user_id                 = get_id_by_mentee(mentee)
    print(user_id)
    sql                     = "insert into {0} (todo_id, mentee, status, start, end, comment, user_id) values ('{1}','{2}','{3}','{4}','{5}','{6}',{7})".format(table_todo, todo_id, mentee, status, start, end, comment, user_id)
    try:
        execute(sql)
        print(sql, flag)
    except:
        flag                = False
        print(sql, flag)
    return flag

# 新規ユーザー登録時に最初のToDo作成
def create_todo_first(name, email, todo_id):
    print("create_todo_first")
    role                    = "メンティ"
    mentee                  = name    
    status                  = "未完了"
    start                   = get_now()
    end                     = ""
    comment                 = ""
    res                     = create_todo(todo_id, role, mentee, status, start, end, comment)
    res                     = send_mail_first_todo(name, email)
    return res

#===================================================
# Twitter API 認証
#===================================================
auth                        = tweepy.OAuthHandler(API_key, API_key_secret)
auth.set_access_token(Access_token, Access_token_secret)
api                         = tweepy.API(auth)

#===================================================
# Flask 初期設定
#===================================================

app                         = Flask(__name__)
app.secret_key              = 'abcdefghijklmn'

#===================================================
# デフォルトルート
#===================================================

#デフォルトルート
@app.route('/')
def default_page():
   return                   redirect("/login")

@app.template_filter('cr')
def cr(arg):
    try:
        return              Markup(arg.replace('\r', '<br>'))
    except:
        return              arg

#===================================================
# ログイン／ログアウト
#===================================================

#ログイン
@app.route('/login')
def login():
    if ('user_name' in session):
        if (session['user_role'] == "メンター"):
            return          redirect("/a_todo_master_list")
        else:
            return          redirect("/todo_todo")
    else:
        return              render_template('login.html')

#ログイン（処理）
@app.route('/login_go', methods=['POST'])
def login_go():
    email                       = request.form.get('email')
    password                    = request.form.get('password')
    res                         = login_check( email , password )
    if (res == "ログイン成功"):
        user_master             = get_user_master_by_email(email)
        name                    = user_master['name']
        role                    = user_master['role']
        session['user_email']   = email
        session['user_name']    = name
        session['user_role']    = role
        if (role == "メンティ"):
            return          redirect("/todo_todo")
        else:
            return          redirect("/a_todo_master_list")
    else:
        return              render_template('login_error.html' , error=res)

#ログアウト
@app.route('/logout')
def logout():
    if ('user_name' in session):
        session.pop('user_name', None)
        session.pop('user_role', None)
        return              redirect("/login")
    else:
        return              render_template('login_error.html' , error="未ログインです")

#===================================================
# パスワード再発行
#===================================================

#パスワード再発行
@app.route('/login_password_reissue')
def password_reissue():
    return                  render_template('password_reissue.html')

#パスワード再発行完了
@app.route('/password_reissue_done')
def password_reissue_done():
    return render_template('login_password_reissue_done.html')

#パスワード再発行（処理）
@app.route('/login_password_reissue_go', methods=['POST'])
def password_reissue_go():
    email                   = request.form.get('email')
    new_password            =  get_random_password()
    
    if (email_check(email) == True):
        sql                 = "update {0} set password='{1}' where email='{2}' ;".format(table_user_master, new_password, email)
        res                 = execute(sql)
        res                 = send_mail_password_reissue()
        return              redirect("/login_password_reissue_done")
    else:
        res                 = "アカウント：{0}は未登録です".format(email)
        return              render_template('login_error.html' , error=res)

#===================================================
# パスワード変更
#===================================================

#パスワード変更
@app.route('/login_password_change')
def password_change():
    if ('user_name' in session):
        user_email          = session['user_email']
        return              render_template('login_password_change.html' , email = user_email )
    else:
        res                 = "ログイン後にパスワード変更が可能です"
        return              render_template('login_error.html' , error=res)

#パスワード変更（処理）
@app.route('/login_password_change_go', methods=['POST'])
def password_change_go():
    email                   = request.form.get('email')
    pwd_old                 = request.form.get('password_old')
    pwd_new                 = request.form.get('password_new')
    res                     = change_password(email, pwd_old, pwd_new)
    if ( res == True ):
        role = session['user_role']
        if (role == "メンティ"):
            return          redirect("/todo_todo")
        else:
            return          redirect("/a_todo_master_list")
    else:
        return              render_template('login_password_change_error.html')

#===================================================
# プロフィール変更
#===================================================

# ユーザー更新
@app.route('/user_master_edit')
def user_master_edit():
    email                   = session['user_email']
    user_master             = get_user_master_by_email(email)
    return                  render_template('u_user_master_edit.html', user=user_master)

# ユーザー更新（処理）
@app.route('/user_master_update', methods=['POST'])
def user_master_update():
    user_id                 = request.form.get('id')
    email                   = request.form.get('email')
    name                    = request.form.get('name')
    twitter                 = request.form.get('twitter')
    twitter                 = twitter.replace('@', '')
    twitter                 = twitter.replace('https://twitter.com/', '')
    sql                     = "update {0} set name = '{1}' , email = '{2}' , twitter = '{3}' where id ='{4}' ; ".format(table_user_master , name , email , twitter , user_id )
    res                     = execute(sql)
    sql                     = "update {0} set mentee='{1}' where user_id='{2}';".format(table_todo, name, user_id)
    res                     = execute(sql)
    session['user_email']   = email
    session['user_name']    = name
    sql                     = "update {0} set mentee='{1}' where user_id='{2}' ; ".format( single_todo_table , name , user_id )
    res                     = execute(sql)
    return                  redirect("/todo_todo")

#===================================================
# ToDo
#===================================================

# Todo　通常一覧
@app.route('/todo_todo')
def todo_todo():
    if ('user_name' in session):
        name                = session['user_name']
        email               = session['user_email']
        user_master         = get_user_master_by_email(email)
        twitter             = user_master['twitter']

        conn                = get_connection()
        c                   = conn.cursor()        
        sql                 = "select * from {0} where email='{1}' order by todo_id desc;".format(view_todo,email)
        c.execute(sql)
        result              = c.fetchall()
        conn.close()
        
        page                = request.args.get(get_page_parameter(), type=int, default=1)
        page_max            = 5
        res                 = result[(page  - 1)*page_max: page*page_max]
        pagination          = Pagination(page=page, total=len(result) ,  per_page=page_max , css_framework='bootstrap4')
        
        return              render_template('u_todo_todo.html', rows=res, name=name, twitter=twitter, pagination=pagination)
    
    else:
        return              redirect("/login")

# Todo　臨時一覧
@app.route('/todo_single_todo')
def todo_single_todo():
    if ('user_name' in session):
        name                = session['user_name']
        email               = session['user_email']
        user_master         = get_user_master_by_email(email)
        twitter             = user_master['twitter']

        conn                = get_connection()
        c                   = conn.cursor()        
        sql                 = "select * from {0} where email='{1}' order by todo_id desc;".format(view_single_todo,email)
        c.execute(sql)
        result              = c.fetchall()
        conn.close()
        
        page                = request.args.get(get_page_parameter(), type=int, default=1)
        page_max            = 50
        res                 = result[(page  - 1)*page_max: page*page_max]
        pagination          = Pagination(page=page, total=len(result) ,  per_page=page_max , css_framework='bootstrap4')
        
        return              render_template('u_todo_single_todo.html', rows=res, name=name, twitter=twitter, pagination=pagination)
    else:
        return              redirect("/login")

#===================================================
# ToDo 更新
#===================================================
    
# ToDo 更新（処理）
@app.route('/todo_update', methods=['POST'])
def todo_update():
    user_id                 = request.form.get('user_id')
    todo_id                 = request.form.get('todo_id')
    mentee                  = request.form.get('mentee')
    now                     = get_now()
    next_todo_id            = get_todo_master_next_todo_id(todo_id)
    
    sql1                    = "update {0} set status='完了', end='{1}' where todo_id='{2}' and user_id={3};".format(table_todo,now,todo_id,user_id)
    flag1                   = execute(sql1)
    
    sql2                    = "insert into {0} (user_id, todo_id, mentee, status , start, end) values ({1},'{2}','{3}','{4}','{5}','');".format(table_todo, user_id, next_todo_id, mentee, '未完了', now)
    flag2                   = execute(sql2)
    
    return                  redirect("/todo_todo")

# ToDo　臨時　更新（処理）
@app.route('/single_todo_update', methods=['POST'])
def single_todo_update():
    todo_id                 = request.form.get('todo_id')
    mentee                  = request.form.get('mentee')
    now                     = get_now()
    
    sql                     = "update {0} set status = '完了', end = '{1}' where todo_id ='{2}' and mentee = '{3}' ; ".format(table_single_todo, now, todo_id, mentee)
    flag                    = execute(sql)

    return                  redirect("/todo_single_todo")

#===================================================
# ユーザーマスタ　一覧
#===================================================

# ユーザー 一覧
@app.route('/a_user_master_list')
def a_user_master():
    if ('user_name' in session):
        conn                = get_connection()
        c                   = conn.cursor()        
        sql                 = "select * from {0};".format(view_user_master_list)
        c.execute(sql)
        result              = c.fetchall()
        conn.close()
        page                = request.args.get(get_page_parameter(), type=int, default=1)
        page_max            = 10
        res                 = result[(page  - 1)*page_max: page*page_max]
        pagination          = Pagination(page=page, total=len(result) ,  per_page=page_max , css_framework='bootstrap4')
        return              render_template('a_user_master_list.html', rows=res, pagination=pagination)
    else:
        return redirect("/login")

#===================================================
# ユーザーマスタ　新規
#===================================================

# ユーザー 新規登録
@app.route('/a_user_master_new')
def a_user_master_new():
    if 'user_name' in session:
        todo_ids        = ["A01","A02","A03"] 
        return          render_template('a_user_master_new.html', ids=todo_ids)
    else:
        return          render_template('login.html')

# ユーザー 新規登録（処理）
@app.route('/a_user_master_new_go', methods=['POST'])
def a_user_master_new_go():
    email               = request.form.get('email')
    name                = request.form.get('name')
    role                = request.form.get('role')
    todo_id             = request.form.get('todo_id')
    twitter             = request.form.get('twitter')
    twitter             = twitter.replace('@', '')
    twitter             = twitter.replace('https://twitter.com/','')
    
    if (todo_id == ""):
        todo_id         = "A01"
        
    password            = get_random_password()

    if (email_check(email) == False):
        res             = create_user_master(email, name, role, password, twitter)
        if (role == "メンティ"):
            try:
                res     = create_todo_first(name,email,todo_id)
            except:
                print("エラー")
    else:
        res             = False
    return redirect("/a_user_master_list")

#===================================================
# ユーザーマスタ　更新
#===================================================

# ユーザー更新
@app.route('/a_user_master_edit', methods=['GET'])
def a_user_master_edit():
    email                   = request.args.get('email')
    user_master             = get_user_master_by_email(email)
    return                  render_template('a_user_master_edit.html', user=user_master)

# ユーザー更新（処理）
@app.route('/a_user_master_update', methods=['POST'])
def a_user_master_update():
    user_id                 = request.form.get('id')
    email                   = request.form.get('email')
    name                    = request.form.get('name')
    password                = request.form.get('password')
    role                    = request.form.get('role')
    followers               = request.form.get('followers')
    twitter                 = request.form.get('twitter')
    twitter                 = twitter.replace('@', '')
    twitter                 = twitter.replace('https://twitter.com/', '')
    
    sql                     = "update {0} set email = '{1}', password='{2}', role='{3}', twitter='{4}', followers='{5}', name='{6}' where id='{7}' ;".format(table_user_master, email, password, role, twitter, followers, name, user_id)
    res                     = execute(sql)
    sql                     = "update {0} set mentee = '{1}' where user_id ='{2}' ;".format(todo_table, name, user_id)
    res                     = execute(sql)
    sql                     = "update {0} set mentee = '{1}' where user_id ='{2}' ;".format(single_todo_table, name, user_id)
    res                     = execute(sql)
    
    return                  redirect("/a_user_master_list")

#===================================================
# ユーザーマスタ　削除
#===================================================

# ユーザー削除（処理）
@app.route('/a_user_master_delete', methods=['GET'])
def a_user_master_delete():
    email                   = request.args.get('email')
    res                     = delete_user_master_by_email(email)
    return                  redirect("/a_user_master_list")

# Twitterフォロワー数の更新
@app.route('/a_user_master_follower_count', methods=['GET'])
def a_user_master_follower_count():
    conn                    = get_connection()
    c                       = conn.cursor()
    sql                     = "select twitter from {0};".format(table_user_master)
    c.execute(sql)
    rows                    = c.fetchall()
    tw = []
    for data in rows:
        twitter             = data[0]
        tw.append(twitter)
    conn.commit()
    conn.close()
    for twitter in tw:
        try:
            user            = api.get_user(screen_name=twitter)
            followers       = user.followers_count
            sql             = "update {0} set followers = '{1}' where twitter = '{2}' ;".format( table_user_master , followers , twitter )
            flag            = execute(sql)
        except:
            print("エラー：ユーザーが見つかりません")
    return              redirect("/a_user_master_list")

#===================================================
# ToDoマスタ 一覧・詳細
#===================================================

# Todoマスタ 一覧
@app.route('/a_todo_master_list')
def a_todo_list():
    if 'user_name' in session:
        conn                = get_connection()
        c                   = conn.cursor()        
        sql                 = "select * from {0};".format(view_todo_master_list)
        c.execute(sql)
        result              = c.fetchall()
        conn.close()
        page                = request.args.get(get_page_parameter(), type=int, default=1)
        page_max            = 50
        res                 = result[(page  - 1)*page_max: page*page_max]
        pagination          = Pagination(page=page, total=len(result) ,  per_page=page_max , css_framework='bootstrap4')
        return              render_template('a_todo_master_list.html', rows=res, pagination=pagination)
    else:
        return redirect("/login")

# Todoマスタ 臨時 一覧
@app.route('/a_single_todo_master_list')
def a_single_todo_master():
    if 'user_name' in session:
        conn                = get_connection()
        c                   = conn.cursor()
        sql                 = "select * from {0};".format(view_single_todo_master_list)
        c.execute(sql)
        result              = c.fetchall()
        conn.close()
        page                = request.args.get(get_page_parameter(), type=int, default=1)
        page_max            = 50
        res                 = result[(page  - 1)*page_max: page*page_max]
        pagination          = Pagination(page=page, total=len(result) ,  per_page=page_max , css_framework='bootstrap4')
        return              render_template('a_single_todo_master_list.html', rows=res, pagination=pagination)
    else:
        return              redirect("/login")

# 管理者用 Todo（通常）：詳細（画面）
@app.route('/a_todo_master_list_details' , methods=['GET'])
def a_todo_list_details():
    if ('user_name' in session):
        todo_id      = request.args.get('todo_id')
        todo         = request.args.get('todo')
        try:
            q_mentee = request.args.get('mentee')
            q_status = request.args.get('status')
        except:
            q_mentee = ""
            q_status = ""
        mentee_list  = get_user_master_mentees()
        conn         = get_connection()
        c            = conn.cursor()
        b            = []
        cmd          = "select todo_id, next_todo_id, todo, name, status, start, end, comment from {0} where todo_id='{1}'".format(view_todo, todo_id)
        query        = []
        if (q_status != "") and (q_status is not None):
            query.append("status = '{0}'".format(q_status))
        if (q_mentee != "") and (q_mentee is not None):
            query.append("mentee = '{0}'".format(q_mentee))
        if len(query) > 0:
            cmd      = cmd + "and " + " and ".join(query)
        cmd          = cmd +  " order by status desc, name asc;"
        print(cmd)
        c.execute(cmd)
        res          = c.fetchall()
        for data in res:
            a        = {'todo_id':data[0], 'next_todo_id':data[1], 'todo':data[2], 'mentee':data[3], 'status':data[4], 'start':data[5], 'end':data[6], 'comment':data[7] }
            b.append(a)
        conn.commit()
        conn.close()
        return render_template('a_todo_master_list_details.html', todo_list=b, query_status=q_status, query_mentee=q_mentee, mentees=mentee_list, todo_id=todo_id, todo=todo)
    else:
        return render_template('login.html')

# 管理者用 Todo（通常）：詳細（画面）
@app.route('/a_single_todo_master_list_details' , methods=['GET'])
def a_single_todo_list_details():
    if ('user_name' in session):
        todo_id      = request.args.get('todo_id')
        todo         = request.args.get('todo')
        try:
            q_mentee = request.args.get('mentee')
            q_status = request.args.get('status')
        except:
            q_mentee = ""
            q_status = ""
        mentee_list  = get_user_master_mentees()
        conn         = get_connection()
        c            = conn.cursor()
        b            = []
        cmd          = "select todo_id, todo, name, status, start, end, comment from {0} where todo_id='{1}'".format(view_single_todo, todo_id)
        query        = []
        if (q_status != "") and (q_status is not None):
            query.append("status = '{0}'".format(q_status))
        if (q_mentee != "") and (q_mentee is not None):
            query.append("mentee = '{0}'".format(q_mentee))
        if len(query) > 0:
            cmd      = cmd + "and " + " and ".join(query)
        cmd          = cmd +  " order by status desc, name asc;"
        print(cmd)
        c.execute(cmd)
        res          = c.fetchall()
        for data in res:
            a        = {'todo_id':data[0], 'todo':data[1], 'mentee':data[2], 'status':data[3], 'start':data[4], 'end':data[5], 'comment':data[6] }
            b.append(a)
        conn.commit()
        conn.close()
        return render_template('a_single_todo_master_list_details.html', todo_list=b, query_status=q_status, query_mentee=q_mentee, mentees=mentee_list, todo_id=todo_id, todo=todo)
    else:
        return render_template('login.html')

#===================================================
# ToDoマスタ 新規
#===================================================

# ToDoマスタ　新規登録
@app.route('/a_todo_master_new')
def a_todo_master_new():
    return              render_template('a_todo_master_new.html')

# ToDoマスタ臨時　新規登録
@app.route('/a_single_todo_master_new')
def a_single_todo_master_new():
    return              render_template('a_single_todo_master_new.html' )

# 登録（処理）
@app.route('/a_todo_master_new_go', methods=['POST'])
def a_todo_master_new_go():
    task_id             = request.form.get('todo_id')
    next_id             = request.form.get('next_todo_id')
    todo                = request.form.get('todo')
    todo_details        = request.form.get('todo_details')
    sql                 = "insert into {0} (todo_id,next_todo_id,todo,todo_details) values ('{1}','{2}','{3}','{4}')".format(table_todo_master,task_id,next_id,todo,todo_details)
    execute(sql)
    return              redirect("/a_todo_master_list")

# ToDoマスタ臨時　新規登録（処理）
@app.route('/a_single_todo_master_new_go', methods=['POST'])
def a_single_todo_master_new_go():
    todo_id             = request.form.get('todo_id')
    exp_date            = request.form.get('exp_date')
    todo                = request.form.get('todo')
    todo_details        = request.form.get('todo_details')
    sql                 = "insert into {0} (todo_id, todo, todo_details, exp_date) values ('{1}', '{2}', '{3}','{4}')".format(table_single_todo_master, todo_id, todo, todo_details, exp_date)
    res                 = execute(sql)
    return              redirect("/a_single_todo_master_list")

#===================================================
# ToDoマスタ 更新
#===================================================

# 更新
@app.route('/a_todo_master_edit', methods=['GET'])
def a_todo_master_edit():
    todo_id             = request.args.get('todo_id')
    todo_info           = get_todo_master(todo_id)
    return              render_template('a_todo_master_edit.html', todo=todo_info)

# 更新（処理）
@app.route('/a_todo_master_update', methods=['POST'])
def a_todo_master_update():
    todo_id             = request.form.get('todo_id')
    next_todo_id        = request.form.get('next_todo_id')
    todo                = request.form.get('todo')
    todo_details        = request.form.get('todo_details')
    todo_details        = todo_details.replace("'","$")
    todo_details        = todo_details.replace('"','#')
    sql                 = "update {0} set next_todo_id='{1}', todo = '{2}', todo_details='{3}' where todo_id='{4}';".format(table_todo_master, next_todo_id, todo, todo_details, todo_id)
    res                 = execute(sql)
    print(sql)
    print(res)
    return              redirect("/a_todo_master_list")

# ToDoマスタ臨時　更新
@app.route('/a_single_todo_master_edit', methods=['GET'])
def a_single_todo_master_edit():
    todo_id             = request.args.get('todo_id')
    todo_info           = get_single_todo_master(todo_id)
    
    return render_template('a_single_todo_master_edit.html', todo=todo_info, todo_id=todo_id)

# ToDoマスタ臨時　更新（処理）
@app.route('/a_single_todo_master_update', methods=['POST'])
def a_single_todo_master_update():
    todo_id             = request.form.get('todo_id')
    todo                = request.form.get('todo')
    exp_date            = request.form.get('exp_date')
    todo_details        = request.form.get('todo_details')
    try:
        todo_details    = todo_details.replace("'","$")
        todo_details    = todo_details.replace('"','#')
    except:
        print("エラー：NoneType")
    sql                 = "update {0} set todo ='{1}', exp_date ='{2}', todo_details='{3}' where todo_id='{4}'".format(table_single_todo_master, todo, exp_date, todo_details, todo_id)
    res                 = execute(sql)
    print(sql)
    print(str(res))
    return              redirect("/a_single_todo_master_list")

#===================================================
# ToDoマスタ 削除
#===================================================

# 削除（処理）
@app.route('/a_todo_master_delete', methods=['GET'])
def a_todo_master_delete():
    todo_id                 = request.args.get('todo_id')
    sql                     = "delete from {0} where todo_id ='{1}'".format(table_todo_master, todo_id)
    execute(sql)
    return                  redirect("/a_todo_master_list")

# ToDoマスタ臨時　削除（処理）
@app.route('/a_single_todo_master_delete', methods=['GET'])
def a_single_todo_master_delete():
    todo_id                 = request.args.get('todo_id')
    sql                     = "delete from {0} where todo_id ='{1}'".format(table_single_todo_master, todo_id)
    res                     = execute(sql)
    return                  redirect("/a_single_todo_master_list")

#===================================================
# ToDo　割り当て 
#===================================================

def get_id_by_mentee(name):
    conn                    = get_connection()
    c                       = conn.cursor()
    sql                     = "select id from {0} where name = '{1}' ; ".format(table_user_master, name)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        user_id             = data[0]
    conn.commit()
    conn.close()
    return                  user_id

# ユーザーマスタのメンティのリストを取得
def get_user_master_mentees():
    conn                    = get_connection()
    c                       = conn.cursor()
    a                       = []
    sql                     = "select name from {0} where role = 'メンティ' ; ".format(table_user_master)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        a.append(data[0])
    conn.commit()
    conn.close()
    return                  a

# ToDo IDを取得
def get_todo_master_ids():
    conn                    = get_connection()
    c                       = conn.cursor()
    a                       = []
    sql                     = "select todo_id from {0}; ".format(table_todo_master)
    c.execute(sql)
    rows                    = c.fetchall()
    for data in rows:
        a.append(data[0])
    conn.commit()
    conn.close()
    return                  a

# ToDoの割り当て
@app.route('/a_todo_master_assignment')
def a_todo_assignment():
    todo_id             = get_todo_master_todo_ids()
    return              render_template('a_todo_master_assignment.html',        todo_ids=todo_id)

# ToDoの割り当て
@app.route('/a_single_todo_master_assignment')
def a_single_todo_assignment():
    todo_id             = get_single_todo_master_todo_ids()
    return              render_template('a_single_todo_master_assignment.html', todo_ids=todo_id)

# ToDoの割り当て（処理）
@app.route('/a_todo_master_assignment_go', methods=['POST'])
def a_todo_assignment_go():
    todo_id             = request.form.get('todo_id')
    mentee              = request.form.get('mentee')
    status              = "未完了"
    start               = get_now()
    end                 = ""
    comment             = ""
    if (mentee == "全ユーザー"):
        for mentee in get_user_master_mentees():
            user_id     = get_id_by_mentee(mentee)
            sql         = "insert into {0} (todo_id, mentee, status, start, end, comment, user_id) values ('{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(table_todo, todo_id, mentee, status, start, end, comment, user_id )
            res         = execute(sql)
    else:
        user_id         = get_id_by_mentee(mentee)
        sql             = "insert into {0} (todo_id, mentee, status, start, end, comment, user_id) values ('{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(table_todo, todo_id, mentee, status, start, end, comment, user_id )
        res             = execute(sql)
    return              redirect("/a_todo_master_list")

# ToDo（臨時）の割り当て（処理）
@app.route('/a_single_todo_master_assignment_go', methods=['POST'])
def a_single_todo_assignment_go():
    todo_id             = request.form.get('todo_id')
    mentee              = request.form.get('mentee')
    status              = "未完了"
    start               = get_now()
    end                 = ""
    comment             = ""
    if (mentee == "全ユーザー"):
        for mentee in get_user_master_mentees():
            user_id     = get_id_by_mentee(mentee)
            sql         = "insert into {0} (todo_id, mentee, status, start, end, comment, id) values ('{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(table_single_todo, todo_id, mentee, status, start, end, comment, user_id )
            res         = execute(sql)
    else:
        user_id         = get_id_by_mentee(mentee)
        sql             = "insert into {0} (todo_id, mentee, status, start, end, comment, id) values ('{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(table_single_todo, todo_id, mentee, status, start, end, comment, user_id )
        res             = execute(sql)
    return              redirect("/a_single_todo_master_list")

#===================================================
# メイン
#===================================================

if __name__ == "__main__":
    port_number         = 5000
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
