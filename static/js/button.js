// JavaScript 代码
function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    hideButton();
}

function guideButton() {
    if (window.location.pathname === '/') {
        window.location.href = '/common';
    } else {
        window.location.href = '/';
    }
}
function showButton() {
    document.querySelector(".icon.black.down111").style.display = "flex";
}

function hideButton() {
    document.querySelector(".icon.black.down111").style.display = "none";
}

function checkScrollPosition() {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
    const clientHeight = document.documentElement.clientHeight || document.body.clientHeight;

    // 计算距离底部的距离
    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);

    // 如果距离底部小于1000像素，则隐藏按钮
    if (distanceFromBottom < 1000) {
        hideButton();
    } else {
        showButton();
    }
}

// 监听滚动事件
window.addEventListener("scroll", checkScrollPosition);

// 初始化
checkScrollPosition();

// 绑定点击事件
document.querySelector(".icon.black.down111").addEventListener("click", scrollToBottom);

document.querySelector(".icon.black.other_com").addEventListener("click", guideButton);


// 绑定登录按钮事件
var ele = document.querySelector(".login_button")
if (ele!==null){
ele.addEventListener("click", function() {
    window.location.href = "/login";
    });};
// 绑定退出登录事件
const ele2 = document.querySelector(".icon.black.logout");
if (ele2 !== null) {
    ele2.addEventListener("click", async () => {
        if (window.confirm('你要退出账号吗？退出按确定')) {
        try {
            const response = await fetch('logout', {
                method: 'GET',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // 可以在这里处理响应
            notyf.success('退出成功')
            window.location.href = "/";
        } catch (error) {
            notyf.error('Error:', error);
        }
    }});
};
