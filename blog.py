import os
import sqlite3

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['DB_PATH'] = "/home/kang/PycharmProjects/flask_blog/blog.db"
app.config['HAS_INIT_DB'] = True
app.config['USER_NAME'] = 'kaka'
app.config['USER_PASSWD'] = '2333'
app.config['UPLOAD_FOLDER'] = "/home/kang/PycharmProjects/flask_blog/static/up_down_load"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


class HighlightRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                   mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = html.HtmlFormatter()
        return highlight(code, lexer, formatter)


renderer = HighlightRenderer()
markdown = mistune.Markdown(renderer=renderer)


@app.route('/')
def index():
    posts = get_posts()
    return render_template("index.html", posts=posts)


@app.route('/download/<string:src>')
def download(src):
    return send_from_directory(app.config['UPLOAD_FOLDER'], src)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join((app.config['UPLOAD_FOLDER']), filename))
        return redirect(url_for('files'))
    return redirect(url_for('error'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/error')
def error():
    return render_template("error.html")


@app.route('/files')
def files():
    dir_files = []
    for i in os.listdir(app.config['UPLOAD_FOLDER']):
        dir_files.append(i)
    return render_template("fileManager.html", files=dir_files)


@app.route('/post/<int:post_id>')
def post(post_id):
    poster = get_post(post_id)
    poster['content'] = markdown(poster['content'])
    return render_template("post.html", post=poster)


@app.route('/add', methods=['POST'])
def add():
    add_post(request.form['title'], request.form['subtitle'], request.form['content'], request.form['tags'],
             sqlite3.Date.today())
    return redirect(url_for('index'))


@app.route('/edit')
def edit():
    return render_template("edit.html")


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    delete_post(post_id)
    return redirect(url_for('index'))


def add_post(title, subtitle, content, tags, post_date):
    db = get_db()
    db.execute("INSERT INTO posts (title,subtitle,content,tags,post_date) VALUES(?,?,?,?,?)"
               , [title, subtitle, content, tags, post_date])
    db.commit()


def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
    db.commit()


def get_posts():
    cursor = get_cursor().execute("SELECT post_id, title, subtitle, tags, post_date FROM posts ORDER BY post_id DESC ")
    return [dict(post_id=row[0], title=row[1], subtitle=row[2], tags=row[3], date=row[4]) for row in cursor.fetchall()]


def get_post(pots_id):
    cursor = get_cursor().execute(
        "SELECT post_id, title, subtitle, content, tags, post_date FROM posts WHERE post_id=?", (pots_id,))
    poster = cursor.fetchone()
    return dict(post_id=poster[0], title=poster[1], subtitle=poster[2], content=poster[3], tags=poster[4],
                date=poster[5])


def get_db():
    connect = sqlite3.connect(app.config['DB_PATH'])
    connect.row_factory = sqlite3.Row
    if not app.config['HAS_INIT_DB']:
        init_db()
    return connect


def init_db():
    db = sqlite3.connect(app.config['DB_PATH'])
    cursor = db.cursor()
    if not app.config['HAS_INIT_DB']:
        sql = app.open_resource("db.sql").read()
        cursor.executescript(sql.decode("utf-8"))
        db.commit()


def get_cursor():
    return get_db().cursor()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
