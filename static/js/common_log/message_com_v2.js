document.addEventListener("DOMContentLoaded", function () {
    // 获取目标 div
    const targetDiv = document.querySelector('.p-6.space-y-6');

    var socket = io();

    // 将 socket 挂载到全局对象 window 上
    window.socket = socket;

    socket.on('connect', function() {
                console.log('WebSocket connection opened:', event);
            });

    // 监听 message 事件
    socket.on('message_com', function (event) {
        const data = JSON.parse(event.data);
        max_log_id = event.new_id
        // 确保 data 是一个数组
        if (!Array.isArray(data)) {
            console.error('Data is not an array:', data);
            return;
        }


        // 遍历数据中的每一项
        data.forEach(item => {
            // 获取目标元素的所有子元素
            var childElements = document.querySelectorAll('.p-4.rounded-lg.border.bg-blue-50.shadow-sm.transition-all.duration-300');
            // 访问最后一个子元素
            var lastChildElement = childElements[childElements.length - 1];
            var last_id = lastChildElement.id;

            if (item.id <= last_id) {
                return;
            }

            // 创建外层div
            var outerDiv = document.createElement('div');
            outerDiv.className = 'p-4 rounded-lg border bg-blue-50 shadow-sm transition-all duration-300 hover:shadow-md';
            outerDiv.id = item.id;

            // 创建内层div
            var innerDiv = document.createElement('div');
            innerDiv.className = 'flex items-start';

            // 创建p标签
            var p = document.createElement('p');
            p.className = 'text-lg break-words';
            p.textContent = `[${item.t}]${item.log_string}`;
            p.style.whiteSpace = 'pre-wrap';

            // 将p元素添加到内层div
            innerDiv.appendChild(p);

            // 将内层div添加到外层div
            outerDiv.appendChild(innerDiv);

            // 将外层div添加到容器
            targetDiv.appendChild(outerDiv);
        });
    });
      // 定义一个发送心跳的函数
    function sendHeartbeat() {
        socket.emit('data_get_com', max_log_id);
    }

    // 设置心跳间隔
    const HEARTBEAT_INTERVAL = 1000; // 每 1 秒发送一次心跳

    // 初始化心跳定时器
    setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
});