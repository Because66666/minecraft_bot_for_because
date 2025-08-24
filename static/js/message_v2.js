document.addEventListener("DOMContentLoaded", function () {
    // 获取目标 div
    const targetDiv = document.querySelector('.bg-gray-100.p-4');

    var socket = io();

    // 将 socket 挂载到全局对象 window 上
    window.socket = socket;

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


        // 遍历数据中的每一项
        data.forEach(item => {
            // 获取目标元素的所有子元素
            var childElements = document.querySelectorAll('.flex.items-start.space-x-2.mb-4');
            // 访问最后一个子元素
            var lastChildElement = childElements[childElements.length - 1];
            var last_id = lastChildElement.id;

            if (item.id <= last_id) {
                return;
            }

            // 创建新的 div 元素
            const newDiv = document.createElement('div');
            newDiv.className = 'flex items-start space-x-2 mb-4';
            newDiv.id = item.id;

            // 创建 span 元素
            const span = document.createElement('span');
            span.className = 'relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full';

            // 创建 img 元素
            const img = document.createElement('img');
            img.className = 'aspect-square h-full w-full';
            img.alt = 'User Avatar';
            img.src = "/static/img/"+item.img_path;

            // 将 img 添加到 span 中
            span.appendChild(img);

            // 将 span 添加到 newDiv 中
            newDiv.appendChild(span);

            // 创建内部的 div 元素
            const innerDiv = document.createElement('div');
            innerDiv.className = 'flex flex-col space-y-1';

            // 创建第一个内部 div
            const firstInnerDiv = document.createElement('div');
            firstInnerDiv.className = 'flex items-center space-x-2';

            // 创建文本 span
            const textSpan = document.createElement('span');
            textSpan.className = 'text-gray-500';
            textSpan.textContent = item.who_string;

//            // 创建 SVG 元素
//            const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
//            svg.setAttribute('width', '24');
//            svg.setAttribute('height', '24');
//            svg.setAttribute('viewBox', '0 0 24 24');
//            svg.setAttribute('fill', 'none');
//            svg.setAttribute('stroke', 'currentColor');
//            svg.setAttribute('stroke-width', '2');
//            svg.setAttribute('stroke-linecap', 'round');
//            svg.setAttribute('stroke-linejoin', 'round');
//
//            // 创建 SVG 路径
//            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
//            path.setAttribute('d', 'M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z');
//
//            // 将路径添加到 SVG
//            svg.appendChild(path);
//
//            // 将文本 span 和 SVG 添加到第一个内部 div
            firstInnerDiv.appendChild(textSpan);
//            firstInnerDiv.appendChild(svg);

            // 创建第二个内部 div
            const secondInnerDiv = document.createElement('div');
            secondInnerDiv.className = 'bg-white p-2 rounded-md shadow-sm';
            const p = document.createElement('p');
            p.textContent = item.log_string;
            secondInnerDiv.appendChild(p);

            // 创建时间 span
            const timeSpan = document.createElement('span');
            timeSpan.className = 'text-xs text-gray-400';
            timeSpan.textContent = item.t;

            // 将所有元素添加到内部的 div
            innerDiv.appendChild(firstInnerDiv);
            innerDiv.appendChild(secondInnerDiv);
            innerDiv.appendChild(timeSpan);

            // 将内部的 div 添加到 newDiv
            newDiv.appendChild(innerDiv);

            // 将 newDiv 添加到目标 div
            targetDiv.appendChild(newDiv);
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