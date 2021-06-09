from flask import Flask, render_template, request, jsonify, redirect, url_for
import jwt
from bson import ObjectId
from pymongo import MongoClient
import hashlib
import datetime

# Server
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'HANGHAE213'

# DB
# client = MongoClient('localhost', 27017)
client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.horror


@app.route('/')
def main():
    token_receive = request.cookies.get('my_token')
    print(token_receive)
    try:
        # 복호화
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"user": payload['id']}, {"pw": 0})

        movies = list(db.movie.find({}).sort("like", -1).limit(30))
        doc = []
        for movie in movies:
            id = (str(ObjectId(movie['_id'])))
            doc.append({
                '_id': id,
                'title': movie['title'],
                'img': movie['img'],
                'url': movie['url'],
                'like': movie['like'],
                'like_by_me': False,
            })
        print(doc)
        user_id = str(user_info['_id'])
        print(user_id)
        return render_template("index.html", movies=doc, user_id=user_id)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except AttributeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/register')
def register():
    return render_template('register.html')

# [로그인 API]
@app.route('/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    result = db.user.find_one({'user': id_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 24)
            # 지금 + 24시간까지 유효하다.
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# [회원가입 API]
@app.route('/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'user': id_receive, 'pw': pw_hash})

    return jsonify({'result': 'success'})

# ## 좋아요 API 역할을 하는 부분
@app.route('/like', methods=['POST'])
def like_movie():
    movie_id = request.form['movie_id']
    user_id = request.form['user_id']

    # movie 테이블 업데이트
    target_movie = db.movie.find_one(ObjectId(movie_id))
    current_like_num = target_movie['like']
    new_like_num = current_like_num + 1
    db.movie.update_one({'_id': ObjectId(movie_id)}, {'$set': {'like': new_like_num}})

    # like 테이블 추가
    doc = {
        'movie_id': ObjectId(movie_id),
        'user_id': ObjectId(user_id),
    }
    db.like.insert_one(doc)
    return jsonify({'msg': '좋아요 완료!', 'result': "success"})


## 좋아요 취소 API 역할을 하는 부분
@app.route('/unlike', methods=['POST'])
def delete_movie():
    movie_id = request.form['movie_id']
    user_id = request.form['user_id']

    # movie 테이블 업데이트
    target_movie = db.movie.find_one(ObjectId(movie_id))
    current_like_num = target_movie['like']
    new_like_num = current_like_num - 1
    db.movie.update_one({'_id': ObjectId(movie_id)}, {'$set': {'like': new_like_num}})

    # like 테이블 삭제
    db.like.delete_one({'movie_id': ObjectId(movie_id), 'user_id': ObjectId(user_id)})

    return jsonify({'msg': '삭제 완료!', 'result': "success"})


@app.route('/detail')
def detail():
    movie_id = request.args.get("movie_id")
    return render_template("movie.html", movie_id=movie_id)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
