document.addEventListener('DOMContentLoaded', function() {
    loadPosts();
    setupAuthButtons();
});

let currentUserId = null;

function loadPosts() {

    fetch('/api', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            method: 'get_current_user',
            params: {},
            id: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result && data.result.is_authenticated) {
            currentUserId = data.result.id;
        }
        fetchPosts();
    })
    .catch(error => {
        console.error('Error fetching current user:', error);
        fetchPosts();
    });
}

function fetchPosts() {

    fetch('/api', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            method: 'get_posts',
            params: {},
            id: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.result){
            renderPosts(data.result);
        } else {
            console.error('Error fetching posts:', data.error);
        }
    })
    .catch(error => {
        console.error('Error fetching posts:', error);
    });
}

function renderPosts(posts) {
    const postsContainer = document.getElementById('posts');
    postsContainer.innerHTML = '';
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');

        const title = document.createElement('h3');
        title.textContent = post.topic;
        postDiv.appendChild(title);

        const content = document.createElement('p');
        content.textContent = post.content;
        postDiv.appendChild(content);

        const author = document.createElement('p');
        author.textContent = `Автор: ${post.author}`;
        postDiv.appendChild(author);

        if (currentUserId && currentUserId === post.user_id) {
            const editButton = document.createElement('button');
            editButton.textContent = 'Редактировать';
            editButton.onclick = () => editPost(post.id);
            postDiv.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Удалить';
            deleteButton.onclick = () => deletePost(post.id);
            postDiv.appendChild(deleteButton);
        }

        postsContainer.appendChild(postDiv);
    });
}

function deletePost(postId) {
    if (!confirm('Вы уверены, что хотите удалить это объявление?')) {
        return;
    }

    fetch('/api', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            method: 'delete_post',
            params: {post_id: postId},
            id: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            alert('Объявление удалено');
            fetchPosts();
        } else {
            alert(`Ошибка: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error deleting post:', error);
    });
}

function editPost(postId) {
    window.location.href = `/edit_post/${postId}`;
}

function setupAuthButtons() {
    const logoutButton = document.getElementById('logout');
    const deleteAccountButton = document.getElementById('delete_account');

    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            fetch('/api', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    method: 'logout',
                    params: {},
                    id: 1
                })
            })
            .then(response => response.json())
            .then(data => {
                if(data.result){
                    window.location.href = '/';
                } else {
                    alert(`Ошибка: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error logging out:', error);
            });
        });
    }

    if (deleteAccountButton) {
        deleteAccountButton.addEventListener('click', function(e) {
            e.preventDefault();
            if(confirm('Вы уверены, что хотите удалить свой аккаунт?')) {
                fetch('/api', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        method: 'delete_account',
                        params: {},
                        id: 1
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if(data.result){
                        alert('Аккаунт удален');
                        window.location.href = '/';
                    } else {
                        alert(`Ошибка: ${data.error}`);
                    }
                })
                .catch(error => {
                    console.error('Error deleting account:', error);
                });
            }
        });
    }
}