function like(movie_id, user_id) {
    console.log(user_id, movie_id)
    $.ajax({
        type: 'POST',
        url: '/like',
        data: {'movie_id': movie_id, 'user_id': user_id},
        success: function (response) {
            if (response.result == 'success') {
                alert(response['msg']);
                window.location.reload();
            }
        }
    });
}

function unlike(movie_id, user_id) {
    $.ajax({
        type: 'POST',
        url: '/unlike',
        data: {'movie_id': movie_id, 'user_id': user_id},
        success: function (response) {
            if (response.result == 'success') {
                alert(response['msg']);
                window.location.reload()
            }
        }
    });
}


function logout(user) {
    let cookies = document.cookie.split(";");
    console.log(cookies);
    let date = new Date();
    date.setDate(date.getDate() - 1);

    let willCookie = "";
    willCookie += `${cookies};`;
    willCookie += "Expires=" + date.toUTCString();

    // 쿠키를 집어넣는다.
    document.cookie = willCookie;

    alert('로그아웃!');
    window.location.href = "/login"
}



