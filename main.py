from flask import Flask,request
from werkzeug.middleware.proxy_fix import ProxyFix
from gevent import pywsgi

app = Flask(__name__)
@app.route('/healthCheck',methods=['Get'])
def health_check():
    print("receive a call")
    return "OK"

if __name__ == "__main__":

    try:
        print("service start")
        app.wsgi_app = ProxyFix(app.wsgi_app)
        app.config['JSON_SORT_KEYS'] = False
        app.config["JSON_AS_ASCII"] = False
        server = pywsgi.WSGIServer(("0.0.0.0",8080),app)
        server.serve_forever()

    except:
        pass
    print("service fail")
