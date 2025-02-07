from flask import render_template, flash, redirect, url_for, request
from app.models import User, FriendShips
from app.forms import LoginForm, RegistrationForm, EditProfileForm, SendFriendRequest
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import app, db


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home Page')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    # ============================================================================================================
    # Запрос на добавление в друзья
    form = SendFriendRequest()
    if form.validate_on_submit():
        existing_request = db.session.scalar(sa.select(FriendShips).where(
            sa.or_(sa.and_(FriendShips.user_id == current_user.id, FriendShips.friend_id == user.id),
                   (sa.and_(FriendShips.user_id == user.id, FriendShips.friend_id == current_user.id)))
        ))
        # existing_request = FriendShips.query.filter_by(user_id=current_user.id, friend_id=user.id).first()
        # Проверка на дружбу
        if existing_request:
            flash('Friend request already sent or user already your friend.', 'warning')
            return redirect(url_for('index'))
        # Создаем новую заявку
        new_request = FriendShips(
            user_id=current_user.id,
            friend_id=user.id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
    # Статус заявки в друзья (если заявки нет status = None)
    status = db.session.scalar(sa.select(FriendShips).where(
        sa.or_(sa.and_(FriendShips.user_id == current_user.id, FriendShips.friend_id == user.id),
               (sa.and_(FriendShips.user_id == user.id, FriendShips.friend_id == current_user.id)))
    ))
    if status is not None:
        status = status.status
    # ============================================================================================================
    return render_template('user.html', user=user, form=form, status=status)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        # current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        # form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/user/<username>/friends', methods=['GET', 'POST'])
@login_required
def friends(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))

    # Друзья пользователя user
    # ============================================================================================================
    data = (db.session.query(User).join(FriendShips, sa.or_(User.id == FriendShips.friend_id,
                                                            User.id == FriendShips.user_id)).filter(
        sa.or_(FriendShips.user_id == user.id, FriendShips.friend_id == user.id),
        FriendShips.status == 'accepted', User.id != user.id).all())
    friends_list = [friend.username for friend in data]
    # ============================================================================================================

    # заявки в друзья для текущего пользователя
    # ============================================================================================================
    # инициализация заявок
    data_friends_requests = (db.session.query(User).join(FriendShips, sa.or_(User.id == FriendShips.friend_id,
                                                                             User.id == FriendShips.user_id)).filter(
        sa.or_(FriendShips.user_id == user.id, FriendShips.friend_id == user.id), FriendShips.status == 'pending',
                                                                                  User.id != user.id).all())
    requests_list = [requests.username for requests in data_friends_requests]

    # Обработка ответов на заявку
    request_friend_status = request.form.get('button_ans_request')
    request_friend_name = request.form.get('friendname')
    print(request_friend_name)
    print(request_friend_status)
    if request_friend_name is not None:
        request_friend = db.first_or_404(sa.select(User).where(User.username == request_friend_name))
        friendship = db.session.query(FriendShips).filter(sa.or_(
            sa.and_((FriendShips.user_id == current_user.id), (FriendShips.friend_id == request_friend.id)),
            sa.and_((FriendShips.user_id == request_friend.id), (FriendShips.friend_id == current_user.id)))).first()
        if friendship:
            friendship.status = request_friend_status
            db.session.commit()
        return redirect(url_for('friends', username=current_user.username))
    # ============================================================================================================
    return render_template('friends.html', title='Friends Page', user=user, friends=friends_list,
                           friends_requests=requests_list)


