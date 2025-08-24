const notyf = new Notyf({
      duration: 1000,
      position: {
        x: 'center',
        y: 'top',
      },
    });

// 获取当前日期
const currentDate = new Date().toISOString();
// 获取 DOM 元素
const messageInput = document.getElementById('messageInput');
const sendMessageBtn = document.getElementById('sendMessageBtn');



// 绑定点击事件
if (sendMessageBtn!==null){
sendMessageBtn.addEventListener('click', async function() {
    // 获取输入框中的内容
    const message = messageInput.value.trim();
    sendMessageBtn.disabled = true;
    // 检查输入框是否为空
    if (message === '') {
        alert('请输入消息内容！');
        return;
    }

    // 发送 POST 请求
    const response = await fetch('/msg_send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    });

    const data = await response.json();
    var status = data.status;
    var msg = data.message;
    if (status === 0){notyf.success(msg);// 使用服务器返回的信息或者默认成功消息
    } else {notyf.error(msg);}


    console.log('Success:', data);
    // 清空输入框
    messageInput.value = '';
    sendMessageBtn.disabled = false;
});
}

