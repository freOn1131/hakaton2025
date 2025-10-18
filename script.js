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
