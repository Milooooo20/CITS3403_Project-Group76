from app import application
from 
    if request.method == 'POST':
        username = request.form.get('username')  
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.profile'))

        flash('Invalid username or password', 'error')
        return redirect(url_for('main.sign_in'))

    return render_template('sign_in.html')