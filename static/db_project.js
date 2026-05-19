let isGalleryActive = false; let galleryAnimationId;
let panTarget = 0; let currentPan = 0; let autoPanSpeed = 1.0; 
let isModalOpen = false; 

let currentDetailArtId = null; let currentDetailArtPrice = 0; let isArtOwnerGlobal = false;
let currentInfoId = null; let currentInfoType = null; let isInfoOwnerGlobal = false;

let currentResId = null; let currentResTotalPrice = 0;
let currentResItemId = null; let currentResItemType = null;

let currentPayType = null; let currentPayId = null;

let currentCommentsData = [];
let currentReviewsData = [];
let currentUserGlobal = null;

function toggleForm() {
    var loginBox = document.getElementById("login-box"); var registerBox = document.getElementById("register-box");
    if (loginBox && registerBox) {
        if (loginBox.style.display !== "none") { loginBox.style.display = "none"; registerBox.style.display = "block"; } 
        else { loginBox.style.display = "block"; registerBox.style.display = "none"; }
    }
}
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar"); var mainContent = document.getElementById("main-content");
    if (sidebar && mainContent) { sidebar.classList.toggle("active"); mainContent.classList.toggle("shifted"); }
}
function loadContent(pageName) {
    fetch(`/api/content/${pageName}`).then(res => res.json()).then(data => {
        var dynamicContent = document.getElementById("dynamic-content"); var mainContent = document.getElementById("main-content"); 
        if(dynamicContent) {
            dynamicContent.innerHTML = data.html;
            if(pageName === 'gallery') {
                mainContent.classList.add('gallery-mode'); isGalleryActive = true; panTarget = 0; currentPan = 0; autoPanSpeed = 1.0; animateGallery();
            } else {
                mainContent.classList.remove('gallery-mode'); isGalleryActive = false; cancelAnimationFrame(galleryAnimationId);
            }
        }
    });
    if(window.innerWidth < 768) toggleSidebar();
}
function openAnyModal(modalId) { var modal = document.getElementById(modalId); if(modal) { modal.style.display = 'flex'; setTimeout(() => modal.classList.add('show'), 10); } }
function closeAnyModal(modalId) { var modal = document.getElementById(modalId); if(modal) { modal.classList.remove('show'); setTimeout(() => modal.style.display = 'none', 300); } }

function submitProfile(event) {
    event.preventDefault(); var formData = new FormData();
    formData.append('fullname', document.getElementById("prof-fullname").value); formData.append('email', document.getElementById("prof-email").value); formData.append('password', document.getElementById("prof-password").value);
    var fileInput = document.getElementById('profile-upload'); if (fileInput && fileInput.files[0]) formData.append('profile_img', fileInput.files[0]);
    fetch('/api/update_profile', { method: 'POST', body: formData }).then(res => res.json()).then(data => {
        var msgBox = document.getElementById("profile-message"); msgBox.textContent = data.message; msgBox.style.color = data.success ? "#27ae60" : "#e74c3c";
        if(data.success) document.getElementById("prof-password").value = ""; 
    });
}
function previewImage(event, targetId, textIdToHide = null) {
    var reader = new FileReader();
    reader.onload = function() { var output = document.getElementById(targetId); output.src = reader.result; output.style.display = 'block'; if(textIdToHide) document.getElementById(textIdToHide).style.display = 'none'; };
    if (event.target.files[0]) reader.readAsDataURL(event.target.files[0]);
}

function submitArt() {
    var title = document.getElementById('art-title').value; var desc = document.getElementById('art-desc').value; var price = document.getElementById('art-price').value; var fileInput = document.getElementById('art-file');
    if (!title || !desc || !price || !fileInput.files[0]) return alert("Eksik alan var.");
    var formData = new FormData(); formData.append('title', title); formData.append('desc', desc); formData.append('price', price); formData.append('art_image', fileInput.files[0]);
    fetch('/api/add_art', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('art-modal'); loadContent('gallery'); } });
}
function submitWorkshop() {
    var title = document.getElementById('w-title').value; var date = document.getElementById('w-date').value; var time = document.getElementById('w-time').value; var price = document.getElementById('w-price').value; var capacity = document.getElementById('w-capacity').value; var desc = document.getElementById('w-desc').value; var fileInput = document.getElementById('w-file');
    if (!title || !fileInput.files[0]) return alert("Afiş ve başlık zorunludur.");
    var formData = new FormData(); formData.append('title', title); formData.append('date', date); formData.append('time', time); formData.append('price', price); formData.append('capacity', capacity); formData.append('desc', desc); formData.append('w_image', fileInput.files[0]);
    fetch('/api/add_workshop', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('workshop-modal'); loadContent('workshops'); } });
}
function submitEvent() {
    var title = document.getElementById('e-title').value; var date = document.getElementById('e-date').value; var time = document.getElementById('e-time').value; var price = document.getElementById('e-price').value; var capacity = document.getElementById('e-capacity').value; var desc = document.getElementById('e-desc').value; var fileInput = document.getElementById('e-file');
    if (!title || !fileInput.files[0]) return alert("Afiş ve başlık zorunludur.");
    var formData = new FormData(); formData.append('title', title); formData.append('date', date); formData.append('time', time); formData.append('price', price); formData.append('capacity', capacity); formData.append('desc', desc); formData.append('e_image', fileInput.files[0]);
    fetch('/api/add_event', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('event-modal'); loadContent('events'); } });
}

// ==========================================
// YORUM VE DEĞERLENDİRME LİSTELEME (FİLTRELİ)
// ==========================================
function fetchComments() {
    fetch(`/api/get_details/${currentDetailArtId}`).then(res => res.json()).then(data => {
        currentCommentsData = data.comments; currentUserGlobal = data.current_user_id; renderComments();
    });
}
function renderComments() {
    var sortBy = document.getElementById('comment-sort') ? document.getElementById('comment-sort').value : 'newest';
    var sorted = [...currentCommentsData];
    if(sortBy === 'highest') sorted.sort((a,b) => b.rating - a.rating);
    else sorted.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));

    var html = '';
    if(sorted.length === 0) html = '<div style="color:#aaa; text-align:center; padding-top:20px;">İlk yorumu sen yap!</div>';
    
    sorted.forEach(c => {
        var deleteMenu = (c.user_id === currentUserGlobal) ? `<div class="three-dots-menu" style="margin-left:auto;"><button class="three-dots-btn">⋮</button><div class="three-dots-content"><a href="#" style="color:red;" onclick="deleteComment(${c.id}); return false;">Sil</a></div></div>` : '';
        var rateSelect = `<select style="margin-left:10px; padding:1px; font-size:11px;" onchange="rateItem('comment', ${c.id}, this.value)"><option>Puanla</option><option value="5">5 ⭐</option><option value="4">4 ⭐</option><option value="3">3 ⭐</option><option value="2">2 ⭐</option><option value="1">1 ⭐</option></select>`;
        var ratingBadge = c.rating > 0 ? `<span style="color:#f1c40f; font-size:12px; margin-left:5px;">⭐ ${c.rating}</span>` : `<span style="color:#ccc; font-size:12px; margin-left:5px;">(Puan Yok)</span>`;
        var ownerReplyHtml = c.reply ? `<div style="margin-top:8px; padding:8px; background:#e8effc; border-left:3px solid #6a89cc; font-size:12px;"><strong>Sanatçı Yanıtı:</strong> ${c.reply}</div>` : '';
        var replyBtnHtml = (isArtOwnerGlobal && !c.reply) ? `<div style="margin-top:5px; text-align:right;"><button style="background:none; border:none; color:#6a89cc; cursor:pointer; font-size:11px; font-weight:bold;" onclick="showReplyInput('comment', ${c.id})">Yanıtla</button></div>` : '';
        
        html += `
        <div style="display:flex; gap:10px; margin-bottom: 12px; align-items: flex-start; width: 100%;">
            <img src="${c.img}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;">
            <div style="background: #fff; padding: 8px 12px; border-radius: 12px; font-size:13px; border: 1px solid #eee; flex-grow:1;">
                <div style="display:flex; align-items:center;">
                    <strong style="color:#444; font-size:12px;">${c.author}</strong>
                    ${ratingBadge} ${c.user_id !== currentUserGlobal ? rateSelect : ''}
                    ${deleteMenu}
                </div>
                <div style="margin-top:5px;">${c.text}</div>
                ${ownerReplyHtml} ${replyBtnHtml}
                <div id="reply-box-comment-${c.id}" style="display:none; margin-top:5px; display:flex; gap:5px;"><input type="text" id="reply-input-comment-${c.id}" placeholder="Yanıtınız..." style="flex-grow:1; padding:5px; font-size:11px;"><button onclick="sendReply('comment', ${c.id})" style="padding:5px; font-size:11px; background:#6a89cc; color:white; border:none; border-radius:4px; cursor:pointer;">Gönder</button></div>
            </div>
        </div>`;
    });
    html = html.replace(/display:flex; gap:5px;"/g, 'display:none; gap:5px;"'); 
    var container = document.getElementById('comments-container'); if(container) container.innerHTML = html;
}

function fetchReviews(type, itemId, containerId) {
    fetch(`/api/get_reviews/${type}/${itemId}`).then(res => res.json()).then(data => {
        currentReviewsData = data.reviews; currentUserGlobal = data.current_user_id; renderReviews(containerId);
    });
}
function renderReviews(containerId) {
    if(!containerId) containerId = 'info-reviews-container';
    var sortBy = document.getElementById('review-sort') ? document.getElementById('review-sort').value : 'newest';
    var sorted = [...currentReviewsData];
    if(sortBy === 'highest') sorted.sort((a,b) => b.rating - a.rating);
    else sorted.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));

    var html = '';
    if(sorted.length === 0) html = '<div style="color:#aaa; text-align:center; padding-top:10px;">Henüz değerlendirme yok.</div>';
    
    sorted.forEach(r => {
        var deleteMenu = (r.user_id === currentUserGlobal) ? `<div class="three-dots-menu" style="margin-left:auto;"><button class="three-dots-btn">⋮</button><div class="three-dots-content"><a href="#" style="color:red;" onclick="deleteReview(${r.id}, '${currentInfoType}', ${currentInfoId}, '${containerId}'); return false;">Sil</a></div></div>` : '';
        var rateSelect = `<select style="margin-left:10px; padding:1px; font-size:11px;" onchange="rateItem('review', ${r.id}, this.value)"><option>Puanla</option><option value="5">5 ⭐</option><option value="4">4 ⭐</option><option value="3">3 ⭐</option><option value="2">2 ⭐</option><option value="1">1 ⭐</option></select>`;
        var ratingBadge = r.rating > 0 ? `<span style="color:#f1c40f; font-size:12px; margin-left:5px;">⭐ ${r.rating}</span>` : `<span style="color:#ccc; font-size:12px; margin-left:5px;">(Puan Yok)</span>`;
        var ownerReplyHtml = r.reply ? `<div style="margin-top:8px; padding:8px; background:#e8effc; border-left:3px solid #6a89cc; font-size:12px;"><strong>Organizatör Yanıtı:</strong> ${r.reply}</div>` : '';
        var replyBtnHtml = (isInfoOwnerGlobal && !r.reply) ? `<div style="margin-top:5px; text-align:right;"><button style="background:none; border:none; color:#6a89cc; cursor:pointer; font-size:11px; font-weight:bold;" onclick="showReplyInput('review', ${r.id})">Yanıtla</button></div>` : '';
        
        html += `
        <div style="display:flex; gap:10px; margin-bottom: 12px; align-items: flex-start; width: 100%;">
            <img src="${r.img}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;">
            <div style="background: #fff; padding: 8px 12px; border-radius: 12px; font-size:13px; border: 1px solid #eee; flex-grow:1;">
                <div style="display:flex; align-items:center;">
                    <strong style="color:#444; font-size:12px;">${r.author}</strong>
                    ${ratingBadge} ${r.user_id !== currentUserGlobal ? rateSelect : ''}
                    ${deleteMenu}
                </div>
                <div style="margin-top:5px;">${r.text}</div>
                ${ownerReplyHtml} ${replyBtnHtml}
                <div id="reply-box-review-${r.id}" style="display:none; margin-top:5px; display:flex; gap:5px;"><input type="text" id="reply-input-review-${r.id}" placeholder="Yanıtınız..." style="flex-grow:1; padding:5px; font-size:11px;"><button onclick="sendReply('review', ${r.id})" style="padding:5px; font-size:11px; background:#6a89cc; color:white; border:none; border-radius:4px; cursor:pointer;">Gönder</button></div>
            </div>
        </div>`;
    });
    html = html.replace(/display:flex; gap:5px;"/g, 'display:none; gap:5px;"'); 
    var container = document.getElementById(containerId); if(container) container.innerHTML = html;
}

function rateItem(type, id, rating) {
    if(rating === "Puanla") return;
    var endpoint = type === 'comment' ? '/api/rate_comment' : '/api/rate_review';
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id, rating: rating }) })
    .then(res => res.json()).then(data => { if(data.success) { if(type === 'comment') fetchComments(); else fetchReviews(currentInfoType, currentInfoId, 'info-reviews-container'); } });
}
function showReplyInput(type, id) { var box = document.getElementById(`reply-box-${type}-${id}`); if(box) box.style.display = 'flex'; }
function sendReply(type, id) {
    var input = document.getElementById(`reply-input-${type}-${id}`); if(!input || input.value.trim() === '') return;
    var endpoint = type === 'comment' ? '/api/reply_comment' : '/api/reply_review';
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id, reply: input.value }) })
    .then(res => res.json()).then(data => { if(data.success) { if(type === 'comment') fetchComments(); else fetchReviews(currentInfoType, currentInfoId, 'info-reviews-container'); } });
}

// YENİ: YÖNETİCİ ÖZET RAPORU GETİRME
function openSummaryReport() {
    var box = document.getElementById('summary-box');
    if(!box) return;
    if(box.style.display === 'block') { box.style.display = 'none'; return; }
    
    fetch(`/api/get_summary/${currentInfoType}/${currentInfoId}`)
    .then(res => res.json()).then(data => {
        if(data.success) {
            document.getElementById('sum-tickets').textContent = data.total_paid_tickets + " / " + data.capacity;
            document.getElementById('sum-revenue').textContent = data.total_revenue + " ₺";
            document.getElementById('sum-rating').textContent = "⭐ " + data.avg_rating + " (" + data.total_reviews + ")";
            box.style.display = 'block';
        }
    });
}

function openDetailModal(id, title, desc, price, img_path, author_name, author_img, like_count, isOwner, isSold) {
    currentDetailArtId = id; currentDetailArtPrice = price; isArtOwnerGlobal = isOwner;
    document.getElementById('detail-img').src = img_path; document.getElementById('detail-title').textContent = title; document.getElementById('detail-desc').textContent = desc; document.getElementById('detail-price').textContent = price + " ₺"; document.getElementById('detail-author-name').textContent = author_name; document.getElementById('detail-author-img').src = author_img; document.getElementById('modal-like-count').textContent = like_count;
    var ownerMenu = document.getElementById('art-owner-menu'); if(ownerMenu) ownerMenu.style.display = isOwner ? 'inline-block' : 'none';
    var buyBtn = document.getElementById('buy-btn'); var soldBadge = document.getElementById('sold-badge');
    if (isSold) { buyBtn.style.display = 'none'; soldBadge.style.display = 'inline-block'; } else { soldBadge.style.display = 'none'; buyBtn.style.display = isOwner ? 'none' : 'inline-block'; }
    document.getElementById('new-comment').value = ''; document.getElementById('comments-container').innerHTML = 'Yükleniyor...';
    fetch(`/api/get_details/${id}`).then(res => res.json()).then(data => {
        var likeBtn = document.getElementById('like-btn'); if (data.user_liked) likeBtn.innerHTML = `❤️ Beğendin (<span id="modal-like-count">${like_count}</span>)`; else likeBtn.innerHTML = `🤍 Beğen (<span id="modal-like-count">${like_count}</span>)`;
        var favBtn = document.getElementById('favorite-btn'); if (data.user_favorited) favBtn.innerHTML = `📌 Favorilerden Çıkar`; else favBtn.innerHTML = `📌 Favoriye Ekle`;
        fetchComments(); 
    });
    openAnyModal('art-detail-modal'); isModalOpen = true; 
}
function closeDetailModal() { closeAnyModal('art-detail-modal'); isModalOpen = false; }
function toggleLike() {
    if(!currentDetailArtId) return;
    fetch('/api/like_art', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId }) })
    .then(res => res.json()).then(data => {
        if(data.success) {
            var likeBtn = document.getElementById('like-btn'); if (data.liked) likeBtn.innerHTML = `❤️ Beğendin (<span id="modal-like-count">${data.new_count}</span>)`; else likeBtn.innerHTML = `🤍 Beğen (<span id="modal-like-count">${data.new_count}</span>)`;
            var floatingBadge = document.getElementById('badge-like-' + currentDetailArtId); 
            // Görüntülenme ve Yorum verisini bozmamak için sadece ❤️ kısmını güncelliyoruz
            if(floatingBadge) floatingBadge.innerHTML = floatingBadge.innerHTML.replace(/❤️ \d+/, '❤️ ' + data.new_count);
        }
    });
}
function toggleFavorite() {
    if(!currentDetailArtId) return;
    fetch('/api/toggle_favorite', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId }) }).then(res => res.json()).then(data => {
        if(data.success) { var favBtn = document.getElementById('favorite-btn'); if (data.favorited) favBtn.innerHTML = `📌 Favorilerden Çıkar`; else favBtn.innerHTML = `📌 Favoriye Ekle`; }
    });
}
function postComment() {
    var text = document.getElementById('new-comment').value; if(text.trim() === '') return;
    fetch('/api/add_comment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId, comment: text }) }).then(res => res.json()).then(data => { if(data.success) { document.getElementById('new-comment').value = ''; fetchComments(); }});
}
function deleteComment(commentId) { fetch('/api/delete_comment/' + commentId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) fetchComments(); }); }
function deleteCurrentArt() { if(confirm('Eser silinecek. Emin misiniz?')) { fetch('/api/delete_art/' + currentDetailArtId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeDetailModal(); loadContent('gallery'); } }); } }

function openInfoModal(id, type, title, desc, date, time, price, capacity, img, author, authorImg, isOwner, reservedTickets, isPast) {
    currentInfoId = id; currentInfoType = type; isInfoOwnerGlobal = isOwner;
    document.getElementById('info-img').src = img; document.getElementById('info-title').textContent = title; document.getElementById('info-desc').textContent = desc; document.getElementById('info-datetime').innerHTML = date + "<br>" + time; document.getElementById('info-price').textContent = price + " ₺"; document.getElementById('info-author-name').textContent = author; document.getElementById('info-author-img').src = authorImg; document.getElementById('info-role').textContent = (type === 'workshop') ? 'Eğitmen' : 'Organizatör';
    var ownerMenu = document.getElementById('info-owner-menu'); if(ownerMenu) ownerMenu.style.display = isOwner ? 'inline-block' : 'none';
    let remaining = capacity - (reservedTickets || 0); document.getElementById('info-capacity').textContent = remaining + " Kişi (Kalan)";
    
    // YÖNETİCİ ÖZET RAPOR KUTUSUNU GİZLE BAŞLAT
    var sumBox = document.getElementById('summary-box'); if(sumBox) sumBox.style.display = 'none';

    let reserveBox = document.getElementById('reservation-box');
    if(reserveBox) {
        if (isPast) reserveBox.innerHTML = '<p style="color:#e74c3c; font-weight:bold; font-size:16px;">⏳ Bu etkinlik sona ermiştir.</p>';
        else if (isOwner) reserveBox.innerHTML = '<p style="color:#666;">Kendi etkinliğinize rezervasyon yapamazsınız.</p>';
        else if (remaining <= 0) reserveBox.innerHTML = '<p style="color:red; font-weight:bold;">❌ Kontenjan Doldu</p>';
        else reserveBox.innerHTML = `<div style="display:flex; justify-content:center; gap:10px; align-items:center;"><label style="font-weight:bold; color:#555;">Kişi Sayısı:</label><input type="number" id="reserve-count" min="1" max="${remaining}" value="1" style="width:60px; padding:8px; border-radius:6px; border:1px solid #ccc;"><button class="btn" style="width:auto; padding:8px 20px; background:#27ae60;" onclick="reserveTickets()">Rezervasyon Yap</button></div>`;
    }
    fetchReviews(type, id, 'info-reviews-container'); openAnyModal('info-detail-modal');
}
function reserveTickets() {
    var count = document.getElementById('reserve-count').value;
    fetch('/api/reserve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: currentInfoId, type: currentInfoType, tickets: count }) }).then(res => res.json()).then(data => { alert(data.message); if(data.success) { closeAnyModal('info-detail-modal'); loadContent('reservations'); }});
}
function deleteCurrentInfo() {
    if(confirm('Silmek istediğinize emin misiniz?')) {
        var route = (currentInfoType === 'workshop') ? '/api/delete_workshop/' : '/api/delete_event/';
        fetch(route + currentInfoId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('info-detail-modal'); loadContent(currentInfoType === 'workshop' ? 'workshops' : 'events'); }});
    }
}

function openReservationModal(resId, title, date, time, price, tickets, img, author, type, itemId, maxAllowed, payStatus, isPast) {
    currentResId = resId; currentResTotalPrice = price * tickets; currentResItemId = itemId; currentResItemType = type;
    document.getElementById('res-img').src = img; document.getElementById('res-title').textContent = title; document.getElementById('res-author').textContent = (type === 'workshop' ? 'Eğitmen: ' : 'Organizatör: ') + author; document.getElementById('res-datetime').innerHTML = date + "<br>" + time; document.getElementById('res-price').textContent = price + " ₺ (Toplam: " + currentResTotalPrice + " ₺)";
    var input = document.getElementById('res-tickets-input'); if(input) { input.max = maxAllowed; input.value = tickets; }
    var payArea = document.getElementById('res-payment-area'); var mngArea = document.getElementById('res-management-area'); var revArea = document.getElementById('res-review-area'); 
    if (isPast) {
        payArea.style.display = 'none'; mngArea.style.display = 'none'; revArea.style.display = 'block'; document.getElementById('new-review').value = ''; fetchReviews(type, itemId, 'reviews-container');
    } else {
        revArea.style.display = 'none';
        if (payStatus === 'Ödendi') { payArea.style.display = 'none'; mngArea.style.display = 'none'; } else { payArea.style.display = 'block'; mngArea.style.display = 'flex'; }
    }
    openAnyModal('reservation-detail-modal');
}
function updateReservation() {
    var tickets = document.getElementById('res-tickets-input').value;
    fetch('/api/update_reservation', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({res_id: currentResId, tickets: tickets}) }).then(res => res.json()).then(data => { alert(data.message); if(data.success) { closeAnyModal('reservation-detail-modal'); loadContent('reservations'); }});
}
function cancelReservation() { if(confirm("Rezervasyonunuzu iptal etmek istediğinize emin misiniz?")) { fetch('/api/cancel_reservation/' + currentResId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('reservation-detail-modal'); loadContent('reservations'); }}); } }

function postReview() {
    var text = document.getElementById('new-review').value; 
    var rating = document.getElementById('new-review-rating').value;
    if(text.trim() === '') return;
    fetch('/api/add_review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_type: currentResItemType, item_id: currentResItemId, review: text, event_rating: rating }) }).then(res => res.json()).then(data => { if(data.success) { document.getElementById('new-review').value = ''; fetchReviews(currentResItemType, currentResItemId, 'reviews-container'); }});
}
function deleteReview(revId, type, itemId, containerId) { fetch('/api/delete_review/' + revId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) fetchReviews(type, itemId, containerId); }); }

function openPaymentModal(type, id, amount) {
    currentPayType = type; currentPayId = id; document.getElementById('payment-amount').textContent = amount + " ₺";
    if(type === 'art') closeAnyModal('art-detail-modal'); if(type === 'reservation') closeAnyModal('reservation-detail-modal');
    openAnyModal('payment-modal');
}
function confirmPayment() {
    fetch('/api/process_payment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: currentPayType, id: currentPayId }) }).then(res => res.json()).then(data => {
        alert(data.message); if(data.success) { closeAnyModal('payment-modal'); if(currentPayType === 'art') loadContent('purchases'); if(currentPayType === 'reservation') loadContent('reservations'); }
    });
}
function animateGallery() {
    if (!isGalleryActive) return;
    var canvas = document.getElementById('gallery-canvas'); var viewport = document.querySelector('.gallery-viewport');
    if (!canvas || !viewport) return;
    var maxPan = Math.max(0, canvas.scrollWidth - viewport.clientWidth);
    if (!isModalOpen) panTarget += autoPanSpeed;
    if (panTarget >= maxPan && autoPanSpeed > 0) autoPanSpeed = -1.0;
    if (panTarget <= 0 && autoPanSpeed < 0) autoPanSpeed = 1.0;
    currentPan += (panTarget - currentPan) * 0.05; canvas.style.transform = `translateX(-${currentPan}px)`;
    galleryAnimationId = requestAnimationFrame(animateGallery);
}
function panGallery(direction) { panTarget += direction * 500; }