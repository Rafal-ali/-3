// NEW: تحديث تلقائي لصفحة المواقف باستخدام Fetch API
function autoRefreshSlots(url, tableId) {
    setInterval(function() {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newTable = doc.getElementById(tableId);
                if (newTable) {
                    document.getElementById(tableId).innerHTML = newTable.innerHTML;
                }
            });
    }, 5000); // تحديث كل 5 ثواني
}
