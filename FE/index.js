const baseUrl = 'http://47.84.52.44:8000';
// const baseUrl = 'http://localhost:8000';
let currentIssueId = null;


document.getElementById('btnLogin').addEventListener('click', function () {
    window.location.href = 'login.html';
});

document.getElementById('btnRegister').addEventListener('click', function () {
    window.location.href = 'register.html';
});

// Kiểm tra đăng nhập
const user_id = localStorage.getItem('id');
const username = localStorage.getItem('username');
if (user_id) {
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

    // 4.1.0 Người dùng đang ở trang index.html có header trạng thái login thành công.
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
        localStorage.clear();
        location.reload();
    });
});


// 1.1.3.	Gọi index.js để gửi mô tả đến generate_image_api.
// 4.1.3 File index.js sẽ gọi hàm sendMessage() 
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('message-input');
    input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            // console.log("enterd")
            sendMessage();
        }
    });
});



// 4.1.1 Người dùng chọn chức năng (Hình ảnh / Nội dung / Slogan).
function toggleMenu() {
    const menu = document.getElementById('options-menu');
    const plusBtn = document.getElementById('plus-button');

    if (!menu || !plusBtn) {
        console.error('Không tìm thấy options-menu hoặc plus-button');
        return;
    }
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

    console.log('sendMessage called');

    const welcomeText = document.getElementById('welcome-text');
    type = document.getElementById('dropdown-label').getAttribute('data-type');

    if (welcomeText) {
        welcomeText.remove();
    }

    const input = document.querySelector('input[type="text"]');
    const message = input.value.trim();
    if (message === '') return;

    // 4.1.3.2 Hiển thị mô tả đã nhập của người dùng (prompt) lên giao diện (phía bên phải của chat-container) trong trang index.html
    const chatContainer = document.getElementById('chat-container');
    const userMsg = document.createElement('div');
    userMsg.className = 'text-right';
    userMsg.innerHTML = `<div class="inline-block bg-blue-100 text-blue-900 px-4 py-2 rounded-2xl">${message}</div>`;
    chatContainer.appendChild(userMsg);

    // 4.1.6 Hiển thị nội dung phản hồi (text hoặc hình ảnh) lên (phía bên trái của chat-container) của trang index.html
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'text-left';
    loadingMsg.id = 'loading-spinner';
    loadingMsg.innerHTML = `<div class="inline-block bg-gray-100 px-4 py-2 rounded-2xl"><div class="loading-spinner"></div></div>`;
    chatContainer.appendChild(loadingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Xóa input
    input.value = '';
    const user_id = localStorage.getItem('id') || null ;

    //1.1.4.	Index.js gửi mô tả đến generate_image_api (http://47.84.52.44:8000/Image).
    // 4.1.3.1 Gửi POST request đến API tương ứng (/content, /slogan, /image) kèm theo dữ liệu của prompt, user_id, issue_id (nếu có).
    fetch(`${baseUrl}/${type}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: message,
            user_id: user_id,
            issue_id: currentIssueId
        })
    })

        //1.1.15    index.js xử lý URL và hiển thị lên index.html
        // 4.1.5 Trang index.html nhận kết quả phản hồi từ save_issue.py (FastAPI).
        .then(response => response.json())
        .then(data => {
            // Xóa spinner loading
            const spinner = document.getElementById('loading-spinner');
            if (spinner) spinner.remove();

            const botMsg = document.createElement('div');
            botMsg.className = 'text-left';
            if (typeof data.data.content === 'string' && data.data.content.startsWith('http') && data.data.content.match(/\.(jpeg|jpg|gif|png|webp)$/)) {
                botMsg.innerHTML = `
                <div class="inline-block bg-gray-100 px-4 py-2 rounded-2xl">
                    <img src="${data.data.content}" alt="Generated Image" class="max-w-xs rounded-lg">
                    <button class="download-btn" onclick="downloadImage('${data.data.content}', 'generated_image.png')">Tải xuống</button>
                </div>
            `;
            } else {
                 //1.4.2. generate_image_api trả về lỗi cho index.js.
                // Trường hợp phản hồi là văn bản bình thường
                const rawText = data.data.content.replace(/\n/g, '<br>');
                botMsg.innerHTML = `
                <div class="inline-block bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl">
                    ${rawText}
                </div>
            `;
            }
            //1.4.3. index.js xử lý lỗi và hiển thị lên index.html
            chatContainer.appendChild(botMsg);
            chatContainer.scrollTop = chatContainer.scrollHeight;

             if (data.data.issue_id && !currentIssueId) {
                currentIssueId = data.data.issue_id;
                console.log('Đã lưu issue_id:', currentIssueId);
                }
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