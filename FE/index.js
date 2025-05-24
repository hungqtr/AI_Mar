// const baseUrl = 'http://47.84.52.44:8000';
const baseUrl = 'http://localhost:8000';

document.getElementById('btnLogin').addEventListener('click', function () {
    window.location.href = 'login.html';
});

document.getElementById('btnRegister').addEventListener('click', function () {
    window.location.href = 'register.html';
});

// Kiểm tra đăng nhập
const username = localStorage.getItem('loggedInUser');
if (username) {
    // Ẩn nút đăng nhập/đăng ký
    document.getElementById('authButtons').classList.add('hidden');

    // Hiển thị avatar với chữ cái viết tắt từ tên đăng nhập
    const initials = username
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase();

    const avatar = document.querySelector('#userAvatar div');
    avatar.textContent = initials;
    document.getElementById('userAvatar').classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', function () {
    const loggedInUser = localStorage.getItem('loggedInUser');
    const avatar = document.getElementById('userAvatar');
    const authButtons = document.getElementById('authButtons');
    const logoutMenu = document.getElementById('logoutMenu');
    const avatarBtn = document.getElementById('avatarBtn');
    const btnLogout = document.getElementById('btnLogout');

    // Hiển thị avatar nếu đã đăng nhập
    if (loggedInUser) {
        avatar.classList.remove('hidden');
        if (authButtons) authButtons.classList.add('hidden');
    }

    // Toggle hiển thị menu khi click avatar
    avatarBtn.addEventListener('click', function (e) {
        e.stopPropagation(); // Ngăn click lan ra ngoài
        logoutMenu.classList.toggle('hidden');
    });

    // Ẩn menu khi click ra ngoài
    document.addEventListener('click', function (e) {
        if (!avatar.contains(e.target)) {
            logoutMenu.classList.add('hidden');
        }
    });

    // Xử lý đăng xuất
    btnLogout.addEventListener('click', function () {
        localStorage.removeItem('loggedInUser');
        location.reload();
    });
});



document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('message-input');
    input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });
});



// Sự kiện ấn nút tùy chọn
function toggleMenu() {
    const menu = document.getElementById('options-menu');
    const plusBtn = document.getElementById('plus-button');

    menu.classList.toggle('hidden');

    // Thêm hoặc gỡ class bg-gray-200 để làm sẫm màu
    if (!menu.classList.contains('hidden')) {
        plusBtn.classList.add('bg-gray-200');
    } else {
        plusBtn.classList.remove('bg-gray-200');
    }
}

//sự kiện chọn loại phản hồi
function selectResponseType(content, type) {
    labelSpan = document.getElementById('dropdown-label');
    labelSpan.innerText = content;
    labelSpan.setAttribute('data-type', type);
    toggleMenu(); 
}

// Hàm tải hình ảnh về máy
function downloadImage(url, filename) {
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = filename || 'generated_image.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        })
        .catch(error => console.error('Lỗi khi tải hình ảnh:', error));
}

function sendMessage() {
    const welcomeText = document.getElementById('welcome-text');
    type = document.getElementById('dropdown-label').getAttribute('data-type');

    if (welcomeText) {
        welcomeText.remove();
    }

    const input = document.querySelector('input[type="text"]');
    const message = input.value.trim();
    if (message === '') return;

    // Hiển thị tin nhắn người dùng
    const chatContainer = document.getElementById('chat-container');
    const userMsg = document.createElement('div');
    userMsg.className = 'text-right';
    userMsg.innerHTML = `<div class="inline-block bg-blue-100 text-blue-900 px-4 py-2 rounded-2xl">${message}</div>`;
    chatContainer.appendChild(userMsg);

    // Thêm spinner loading
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'text-left';
    loadingMsg.id = 'loading-spinner';
    loadingMsg.innerHTML = `<div class="inline-block bg-gray-100 px-4 py-2 rounded-2xl"><div class="loading-spinner"></div></div>`;
    chatContainer.appendChild(loadingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Xóa input
    input.value = '';


        //  3.1.3 Web UI gửi promtp đến API endpoint http://47.84.52.44:8000/content.
    fetch(`${baseUrl}/${type}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: message })
    })

        // 3.1.11 Web UI xử lý nhận và hiển thị nội dung lên cho người dùng.

        .then(response => response.json())
        .then(data => {
            // Xóa spinner loading
            const spinner = document.getElementById('loading-spinner');
            if (spinner) spinner.remove();

            const botMsg = document.createElement('div');
            botMsg.className = 'text-left';
            if (typeof data.data === 'string' && data.data.startsWith('http') && data.data.match(/\.(jpeg|jpg|gif|png|webp)$/)) {
                botMsg.innerHTML = `
                <div class="inline-block bg-gray-100 px-4 py-2 rounded-2xl">
                    <img src="${data.data}" alt="Generated Image" class="max-w-xs rounded-lg">
                    <button class="download-btn" onclick="downloadImage('${data.data}', 'generated_image.png')">Tải xuống</button>
                </div>
            `;
            } else {
                // Trường hợp phản hồi là văn bản bình thường
                const rawText = data.data.replace(/\n/g, '<br>');
                botMsg.innerHTML = `
                <div class="inline-block bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl">
                    ${rawText}
                </div>
            `;
            }
            chatContainer.appendChild(botMsg);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
        .catch(error => {
            // Xóa spinner loading
            const spinner = document.getElementById('loading-spinner');
            if (spinner) spinner.remove();

            console.error('Lỗi khi gọi API:', error);
            const botMsg = document.createElement('div');
            botMsg.className = 'text-left';
            botMsg.innerHTML = `<div class="inline-block bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl">Có lỗi xảy ra, vui lòng thử lại sau.</div>`;
            chatContainer.appendChild(botMsg);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
}