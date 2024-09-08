from webapp import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

print("STARTING PRODUCTION SERVER")

app = create_app()

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
