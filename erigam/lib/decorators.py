from flask import g, render_template, request, abort
from functools import wraps
from erigam.lib.api import ping

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create DB object if it does not exist.
        if not g.user.globalmod:
            return render_template('admin_denied.html')
        return f(*args, **kwargs)
    return decorated_function

def mark_alive(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(g, "chat_type"):
            g.joining = ping(g.redis, request.form['chat'], g.user, g.chat_type)
        else:
            # Abort 404 just in case chat_type isn't defined
            abort(404)

        return f(*args, **kwargs)
    return decorated_function
