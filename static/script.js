let currentTab = 'view';

function showTab(tabName) {
  document.querySelectorAll('.tabcontent').forEach(tc => tc.style.display='none');
  document.getElementById('tab-' + tabName).style.display='block';
}

document.querySelectorAll('.tablink').forEach(btn => 
  btn.addEventListener('click', () => showTab(btn.getAttribute('onclick').match(/'(.*)'/)[1]))
);

function searchOrganization() {
  const input = document.getElementById('searchInput').value;
  const type = document.getElementById('searchType').value;
  // отправка запроса к backend для поиска
  // отображение результатов
}

function loadIndustryReport() {
  const industry = document.getElementById('industrySelect').value;
  // загрузка данных по отрасли
}

function processData() {
  const textData = document.getElementById('rawData').value;
  // отправка текста на парсинг нейросетью
}

function saveData() {
  // сохранить обработанные и сверенные данные в БД по API
}

function downloadPDF() {
  // создание отчета и скачивание
}
async function saveFromFNS(org) {
    const data = {
        inn: org.ИНН || org.inn,
        short_name: org.НаимСокрЮЛ || org.short_name,
        full_name: org.НаимПолнЮЛ || org.full_name,
        status: org.Статус || 'Действующая',
        legal_address: org.АдресПолн || org.legal_address,
        main_okved: org.ОснВидДеят || org.main_okved,
        user_id: currentUser ? currentUser.id : 1
    };
    
    if (!confirm(`Сохранить "${data.short_name}"?`)) return;
    
    try {
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await res.json();
        alert(result.status === 'success' ? 
              `✅ Сохранено! ID: ${result.organization_id}` : 
              `❌ Ошибка: ${result.error}`);
    } catch (e) {
        alert(`❌ ${e.message}`);
    }
}
