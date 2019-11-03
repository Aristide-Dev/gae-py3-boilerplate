from flask import request, abort, make_response, url_for, redirect

from models.app_settings import AppSettings
from models.user import User
from utils.check_environment import is_local
from utils.decorators import public_handler
from utils.translations import render_template_with_translations


@public_handler
def init(**params):
    """Initialize the web app if there's no admin user yet. This is only needed once."""

    # find a user with admin privileges - if such user exists, the web app is already initialized
    if User.is_there_any_admin():
        return "The web app has already been initialized. <a href='/'>Return back to index</a>."

    # else proceed with initialization
    if request.method == "GET":
        params["app_settings"] = AppSettings.get()
        return render_template_with_translations("public/auth/init.html", **params)

    elif request.method == "POST":
        sendgrid_api_key = request.form.get("init-sendgrid")
        email_address = request.form.get("init-email")

        if email_address and sendgrid_api_key:
            AppSettings.update(sendgrid_api_key=sendgrid_api_key)

            User.create(email_address=email_address, admin=True)

            return render_template_with_translations("public/auth/init_success.html", **params)
        else:
            return abort(403)


@public_handler
def login(**params):
    if request.method == "GET":
        return render_template_with_translations("public/auth/login.html", **params)
    elif request.method == "POST":
        email_address = request.form.get("login-email")

        success, message = User.send_magic_login_link(email_address=email_address)

        if success:
            return render_template_with_translations("public/auth/login-magic-link-sent.html", **params)
        else:
            return abort(403, description=message)


@public_handler
def validate_magic_login_link(token, **params):
    if request.method == "GET":
        success, result = User.validate_magic_login_token(magic_token=token, request=request)

        if success:
            # result is session token, store it in a cookie
            # prepare a response and then store the token in a cookie
            response = make_response(redirect(url_for("profile.main.sessions_list")))

            # on localhost don't make the cookie secure and http-only (but on production it should be)
            cookie_secure_httponly = False
            if not is_local():
                cookie_secure_httponly = True

            # store the token in a cookie
            response.set_cookie(key="my-web-app-session", value=result, secure=cookie_secure_httponly,
                                httponly=cookie_secure_httponly)
            return response
        else:
            # result is an error message
            return abort(403, description=result)


@public_handler
def register(**params):
    if request.method == "GET":
        return render_template_with_translations("public/auth/register.html", **params)
