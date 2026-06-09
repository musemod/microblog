# Home page route
from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm


# decorators (modifies the function that follows it)
@app.route('/')
@app.route('/index')

# A common pattern with decorators is to use them to register functions as callbacks for certain events
# In this case, the @app.route decorator creates an association between the URL given as an argument and the function. In this example there are 2 decorators, which associate the URLs / and /index to this function. This means that when a web browser requests either of these 2 URLs, Flask is going to invoke this function and pass its return value back to the browser as a response

def index():
    user = {'username': 'C'} # mock object (mock user - so can keep building and just have a fake user in place temporarily)

    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]

    return render_template('index.html', title='Home', user=user, posts=posts)



#  import render_template() that comes with the Flask framework. This function takes a template filename and a variable list of template arguments, and returns the same template, but with all the placeholders in it replaced with actual values.

# The render_template() function invokes the Jinja template engine that comes bundled with the Flask framework. Jinja substitutes {{ ... }} blocks with the corresponding values, given by the arguments provided in the render_template() call.


#     return f'''
# <html>
#     <head>
#         <title>Home page - Microblog</title>
#     </head>
#     <body>
#         <h1>Hello, {user['username']}!</h1>
#     </body>
# </html>'''


# ALTERNATE version with .format()
# def index():
#     user = {'username': 'C'}
#     return '''
# <html>
#     <head>
#         <title>Home page - Microblog</title>
#     </head>
#     <body>
#         <h1>Hello, {username}!</h1>
#     </body>
# </html>'''.format(username=user['username'])


# decorator
@app.route('/login', methods=['GET', 'POST'])

# function
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


