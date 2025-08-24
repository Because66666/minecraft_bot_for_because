const notyf = new Notyf({
      duration: 3000,
      position: {
        x: 'center',
        y: 'top',
      },
    });

// 获取元素
var element_login = document.querySelector('[data-id="18"]');//登录按钮
var cap = document.querySelector('[data-id="16"]');//验证码按钮
// 是否发送了验证码,true：未发送
window.flag = true;

// 发送POST请求
async function sendPostRequest(username,email) {
    const url2 = '/login_api/send';
    const data = { username,email };
    window.flag = false;
    try {
        const response = await fetch(url2, {
            method: 'POST', // 或 'PUT'
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data), // 将JavaScript对象转换成JSON字符串
        });

        if (!response.ok) {
            notyf.error(`HTTP error! Status: ${response.status}`);
            window.flag = true;
        }

        const responseData = await response.json();
        if (responseData.status !==0) {
        notyf.error(responseData.msg);
        window.flag = true;
        }
        else {notyf.success(responseData.msg);}

        console.log(responseData); // 输出返回的JSON数据
    } catch (error) {
        notyf.error('Error:', error);
        window.flag = true;
    }
}

//验证码按钮
cap.addEventListener("click",async function() {
    // 获取用户名
    var username = document.querySelector('[data-id="11"]').value;
    var email  =document.querySelector('[data-id="11_2"]').value;
    if (window.flag === false) {notyf.error('验证码已经发送'); return;
    }
    if (username === ''){ notyf.error('请输入用户名'); return;
    }
    if (username === 'Because'){ notyf.error('不受支持的用户'); return;
    }
    if (username === 'because'){ notyf.error('不受支持的用户'); return;
    }
    notyf.success('正在发送验证码');
    await sendPostRequest(username,email);

});


//登录按钮
element_login.addEventListener("click",async function() {
    // 获取用户名
    var username = document.querySelector('[data-id="11"]').value;
    if (username === ''){
    notyf.error('请输入用户名');
    return;
    }
    var email = document.querySelector('[data-id="11_2"]').value;
    if (email === ''){
    notyf.error('请输入邮箱地址');
    return;
    }
    var cap_value = document.querySelector('[data-id="15"]').value;
    if (cap_value === ''){
    notyf.error('请输入验证码');
    return;
    }


    var code = cap_value
    const url3 = '/login_api/register';
    const data = { username,code,email };

    try {
        const response = await fetch(url3, {
            method: 'POST', // 或 'PUT'
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data), // 将JavaScript对象转换成JSON字符串
        });

        if (!response.ok) {
            notyf.error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        if (responseData.status !==0) {
        notyf.error(responseData.msg);
        }
        else {
            notyf.success(responseData.msg);
            element_login.disabled = true;
            cap.disabled = true;
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
               }
            await sleep(3000);
            window.location.href = '/';
        }

        console.log(responseData); // 输出返回的JSON数据
    } catch (error) {
        notyf.error('Error:', error);
    }

});