 document.addEventListener('DOMContentLoaded', function() {
    // 当页面加载完成时执行
    document.querySelectorAll('.flex.items-start.space-x-2.mb-4').forEach(function(div) {
      div.addEventListener('click', function(event) {
        // 获取当前点击div下的所有span元素
        var currentSpan = this.querySelector('.text-xs.text-gray-400');

        // 获取页面上所有的span元素
        var allSpans = document.querySelectorAll('.text-xs.text-gray-400');

        // 遍历所有span元素并设置显示/隐藏
        Array.from(allSpans).forEach(function(span) {
          if (span !== currentSpan) {
            // 如果span不属于当前点击的div，则隐藏
            span.style.display = 'none';
          }
        }, this);

      if (window.getComputedStyle(currentSpan).display !== 'none') {
            currentSpan.style.display = 'none';
          } else {
            currentSpan.style.display = 'inline';
        }
        });
    });
        //当用户滑到最顶部的时候
    function checkIfScrolledToTop() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop === 0) {
              // 向服务器发送一个名为 'update_old_log' 的事件及一些数据
              console.log('Sending event "update_old_log"...');
              if (window.location.pathname !=='/common'){
              socket.emit('update_old_log', min_log_id, function(responseFromServer) {
                console.log('Response from server:', responseFromServer);
              });}
              else {
                socket.emit('update_old_log_com', min_log_id, function(responseFromServer) {
                console.log('Response from server:', responseFromServer);
              });
              }

              ;
        }
    }
    document.addEventListener('scroll', function () {
        checkIfScrolledToTop();
});
    function scrollToBottom() {
        // 滚动到底部
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth' // 以平滑的方式滚动
        });
    }
    scrollToBottom();

});

 document.addEventListener('DOMContentLoaded', function() {
         // 滚动到底部
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth' // 以平滑的方式滚动
        });
 });