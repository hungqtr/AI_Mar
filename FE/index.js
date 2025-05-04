const baseUrl = 'http://47.84.52.44:8000';




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
function selectResponseType(content, type ) {
    labelSpan=  document.getElementById('dropdown-label');
    labelSpan.innerText = content;
    labelSpan.setAttribute('data-type', type);
    toggleMenu(); // Ẩn dropdown
}

function sendMessage() {
    const welcomeText = document.getElementById('welcome-text');
    type=  document.getElementById('dropdown-label').getAttribute('data-type');

    if (welcomeText) {
        welcomeText.remove(); // hoặc welcomeText.style.display = 'none';
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

    // Xóa input
    input.value = '';

    fetch(`${baseUrl}/${type}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: message })
    })
    .then(response => response.json())
    .then(data => {
        const botMsg = document.createElement('div');
        botMsg.className = 'text-left';
        if (typeof data.data === 'string' && data.data.startsWith('http') && data.data.match(/\.(jpeg|jpg|gif|png|webp)$/)) {
            botMsg.innerHTML = `
                <div class="inline-block bg-gray-100 px-4 py-2 rounded-2xl">
                    <img src="${data.data}" alt="Generated Image" class="max-w-xs rounded-lg">
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
        console.error('Lỗi khi gọi API:', error);
        const botMsg = document.createElement('div');
        botMsg.className = 'text-left';
        botMsg.innerHTML = `<div class="inline-block bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl">Có lỗi xảy ra, vui lòng thử lại sau.</div>`;
        chatContainer.appendChild(botMsg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });

    
}

