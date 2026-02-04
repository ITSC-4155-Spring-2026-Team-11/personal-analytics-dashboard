(async function () {
  const data = await apiGet("/schedules/today");
  document.getElementById("output").textContent = JSON.stringify(data, null, 2);
})();
