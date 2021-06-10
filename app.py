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
client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.horror


@app.route('/')
def main():
    token_receive = request.cookies.get('mytoken')
    print(token_receive)
    try:
        # 복호화
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"user": payload['id']}, {"pw": 0})
        movies = list(db.movie.find({}).sort("like", -1).limit(30))
        doc = []
        for movie in movies:
            isLiked = db.like.find_one({'user_id': ObjectId(user_info['_id']), 'movie_id': movie['_id']})
            if isLiked:
                id = (str(ObjectId(movie['_id'])))
                doc.append({
                    '_id': id,
                    'title': movie['title'],
                    'img': str(movie['img']).split('?')[0],
                    'url': movie['url'],
                    'like': movie['like'],
                    'like_by_me': True,
                })
            else:
                id = (str(ObjectId(movie['_id'])))
                doc.append({
                    '_id': id,
                    'title': movie['title'],
                    'img': str(movie['img']).split('?')[0],
                    'url': movie['url'],
                    'like': movie['like'],
                    'like_by_me': False,
                })
        print(doc)
        user_id = str(user_info['_id'])
        user = user_info['user']
        # print(user)
        return render_template("index.html", movies=doc, user_id=user_id, user=user)
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

# 아이디 중복 확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.user.find_one({"user": username_receive}))
    print(exists)
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/register')
def register():
    return render_template('register.html')

# [로그인 API]
@app.route('/sign_in', methods=['POST'])
def api_login():
    id_receive = request.form['username_give']
    pw_receive = request.form['password_give']

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
@app.route('/sign_up/save', methods=['POST'])
def api_register():
    id_receive = request.form['username_give']
    pw_receive = request.form['password_give']

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

# ## 좋아요 API 역할을 하는 부분
# @app.route('/liked', methods=['POST'])
# def liked_movie():
#     print('liked here')
#     movie_id = request.form['movie_id']
#     user_id = request.form['user_id']
#
#     try:
#         target_movie = db.like.find_one({'movie_id': ObjectId(movie_id), 'user_id': ObjectId(user_id)})
#         if target_movie is not None:
#             isLiked = True
#             # msg = '좋아요 업데이트 완료'
#             # result = 'success'
#         else:
#             isLiked = False
#             # msg = '좋아요 업데이트 중 문제가 발생했습니다.'
#             # result = 'fail'
#     except:
#         pass
#         # msg = '좋아요 업데이트 중 문제가 발생했습니다.'
#         # result = 'fail'
#         print('isLiked', isLiked)
#     return render_template('index.html', isLiked=isLiked)

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


#################유진 작업공간##################

@app.route('/movie/<movie_id>/<user_id>', methods=['GET'])
def movie(movie_id, user_id):
    movies = list(db.movie.find({'_id': ObjectId(movie_id)}))
    this_movie = {'movie_id': movies[0]['_id'], 'title': movies[0]['title'], 'img': movies[0]['img'].split('?')[0],
                  'url': movies[0]['url'],
                  'like': movies[0]['like'], 'rate': movies[0]['rate'], 'time': movies[0]['time'],
                  'desc': movies[0]['desc']}
    replies = list(db.reply.find({'movie_id': movie_id}))
    # print(this_movie)
    return render_template("movie.html", movie=this_movie, user_id=user_id, replies=replies)


@app.route('/api/save_reply', methods=['POST'])
def save_reply():
    #  저장하기
    now = datetime.datetime.now()  # 시간
    reply_time = now.strftime("%H:%M:%S")  # 댓글시간
    reply_receive = request.form["reply_give"]  # 댓글내용
    # user_id = request.form["user_id_give"]
    movie_id = request.form["movie_id_give"]
    user_id = request.form['user_id_give']
    print(reply_time, reply_receive, movie_id, user_id)
    # doc = {"movie_id":movie_id, "user_id":user_id, "reply": reply_receive, "reply_time": reply_time}
    doc = {"movie_id": movie_id, "user_id": user_id, "reply": reply_receive, "reply_time": reply_time}
    db.reply.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '댓글 등록 완료'})

@app.route('/api/delete_reply', methods=['POST'])
def delete_reply():
    #  삭제하기
    user_id_receive = request.form["user_id_give"]  # 유저id
    movie_id_receive = request.form["movie_id_give"] #영화id
    reply_id_receive = request.form["rely_id_give"] #댓글고유id
    print(reply_id_receive)
    print(user_id_receive)
    print(movie_id_receive)
    db.reply.delete_one({'_id': ObjectId(reply_id_receive)})
    return jsonify({'result': 'success', 'msg': '댓글 삭제 완료'})

##############################################


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
