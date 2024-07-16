from flask import Flask
from livereload import Server
from web_app import app

if __name__ == '__main__':
    app.debug = True
    server = Server(app.wsgi_app)
    server.watch('src/**/*.py')
    server.watch('src/templates/**/*.html')
    server.watch('src/static/**/*.js')
    server.watch('src/static/**/*.css')
    server.serve(port=5000, host='localhost')
