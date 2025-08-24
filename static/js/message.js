document.addEventListener("DOMContentLoaded", function () {
    const tbody = document.querySelector('#logsTable tbody');

    var socket = io();

    socket.on('connect', function() {
                console.log('WebSocket connection opened:', event);
            });

    // 监听 message 事件
    socket.on('message', function (event) {
        const data = JSON.parse(event.data);
        max_log_id = event.new_id
        // 确保 data 是一个数组
        if (!Array.isArray(data)) {
            console.error('Data is not an array:', data);
            return;
        }

        // 获取 tbody 元素
        const tbody = document.getElementById('logTableBody'); // 假设您的表格 body 的 ID 为 logTableBody

        // 遍历数据中的每一项
        data.forEach(item => {
            // 创建新的表格行
            const row = document.createElement('tr');

            const timeCell = document.createElement('td');
            timeCell.textContent = item.t; // 时间戳
            row.appendChild(timeCell);

            const whoCell = document.createElement('td');
            whoCell.textContent = item.who_string; // 用户名
            row.appendChild(whoCell);

            const logCell = document.createElement('td');
            logCell.textContent = item.log_string; // 日志消息
            row.appendChild(logCell);

            tbody.appendChild(row); // 将新行添加到表格中
        });
    });
      // 定义一个发送心跳的函数
    function sendHeartbeat() {
        socket.emit('data_get', max_log_id);
    }

    // 设置心跳间隔
    const HEARTBEAT_INTERVAL = 1000; // 每 1 秒发送一次心跳

    // 初始化心跳定时器
    setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
});