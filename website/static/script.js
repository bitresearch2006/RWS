fetch("/api/services")
  .then(res => res.json())
  .then(services => {
    const container = document.getElementById("services");
    container.innerHTML = "";

    if (services.length === 0) {
      container.textContent = "No services found.";
      return;
    }

    services.forEach(service => {
      const div = document.createElement("div");
      div.className = "service";
      div.innerHTML = `
        <h2>${service.name}</h2>
        <p>${service.description}</p>
        <a href="${service.url}" target="_blank">View on GitHub</a>
      `;
      container.appendChild(div);
    });
  })
  .catch(() => {
    document.getElementById("services").textContent = "Failed to load services.";
  });
