document.addEventListener("DOMContentLoaded", function () {
    // 获取目标 div
    const targetDiv = document.querySelector('.p-6.space-y-6');


    // 监听 message 事件
    window.socket.on('update_old_log_com', function (event) {
        const data = JSON.parse(event.data);
        min_log_id = event.new_id
        // 确保 data 是一个数组
        if (!Array.isArray(data)) {
            console.error('Data is not an array:', data);
            return;
        }


        // 遍历数据中的每一项
        data.forEach(item => {
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


            // 将 newDiv 插入到 targetDiv 的最前面
            if (targetDiv.firstChild) {
                targetDiv.insertBefore(outerDiv, targetDiv.firstChild);
            } else {
                targetDiv.appendChild(outerDiv);  // 如果没有子元素，则直接添加
            }
        });
    });

});