// Main JavaScript for Parking Management System

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  initializeTooltips();

  // Add loading states to forms
  initializeFormLoading();

  // Add smooth animations
  initializeAnimations();

  // Initialize search functionality
  initializeSearch();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// Add loading states to form submissions
function initializeFormLoading() {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML =
          '<i class="bi bi-hourglass-split me-1"></i>Processing...';
        submitBtn.disabled = true;

        // Re-enable after 5 seconds as fallback
        setTimeout(() => {
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }, 5000);
      }
    });
  });
}

// Add smooth animations to cards and elements
function initializeAnimations() {
  // Animate cards on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, observerOptions);

  // Observe all cards
  document.querySelectorAll(".card").forEach((card) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    card.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    observer.observe(card);
  });
}

// Initialize search functionality for tables
function initializeSearch() {
  const searchInputs = document.querySelectorAll(
    'input[placeholder*="Search"]'
  );

  searchInputs.forEach((input) => {
    input.addEventListener("keyup", function () {
      const searchTerm = this.value.toLowerCase();
      const table = this.closest(".card").querySelector("table tbody");

      if (table) {
        const rows = table.querySelectorAll("tr");
        let visibleCount = 0;

        rows.forEach((row) => {
          const text = row.textContent.toLowerCase();
          const isVisible = text.includes(searchTerm);
          row.style.display = isVisible ? "" : "none";
          if (isVisible) visibleCount++;
        });

        // Show/hide empty state
        updateEmptyState(table, visibleCount, searchTerm);
      }
    });
  });
}

// Update empty state for search results
function updateEmptyState(table, visibleCount, searchTerm) {
  let emptyState = table.parentElement.querySelector(".search-empty-state");

  if (visibleCount === 0 && searchTerm) {
    if (!emptyState) {
      emptyState = document.createElement("div");
      emptyState.className = "search-empty-state text-center py-4";
      emptyState.innerHTML = `
                <i class="bi bi-search text-muted" style="font-size: 2rem;"></i>
                <h6 class="text-muted mt-2">No results found</h6>
                <p class="text-muted small mb-0">Try adjusting your search terms</p>
            `;
      table.parentElement.appendChild(emptyState);
    }
    emptyState.style.display = "block";
    table.style.display = "none";
  } else {
    if (emptyState) {
      emptyState.style.display = "none";
    }
    table.style.display = "";
  }
}

// Utility function to show notifications
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
  notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 5000);
}

// Format currency values
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(amount);
}

// Format date/time values
function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Validate phone numbers
function validatePhoneNumber(phone) {
  const phoneRegex = /^[0-9]{10}$/;
  return phoneRegex.test(phone);
}

// Validate email addresses
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Export functions for use in other scripts
window.ParkingSystem = {
  showNotification,
  formatCurrency,
  formatDateTime,
  validatePhoneNumber,
  validateEmail,
};

// --- API helpers that invoke DB functions/procedures via server routes ---
// These call the Flask API endpoints which in turn CALL stored procedures / SELECT functions
async function getAvailableSpots(lotId) {
  try {
    const res = await fetch(`/api/available-spots/${lotId}`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    return data.available;
  } catch (err) {
    console.error("getAvailableSpots error", err);
    showNotification("Failed to fetch available spots", "danger");
    return null;
  }
}

async function swapSpot(ticketId, newSpotNumber) {
  try {
    const res = await fetch("/api/swap-spot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticketId: ticketId,
        newSpotNumber: newSpotNumber,
      }),
    });
    const json = await res.json();
    if (!res.ok || json.status !== "ok") {
      throw new Error(json.message || "Swap failed");
    }
    showNotification("Spot swapped successfully", "success");
    // refresh to show updated spot/occupancy
    setTimeout(() => location.reload(), 700);
    return true;
  } catch (err) {
    console.error("swapSpot error", err);
    showNotification(`Swap failed: ${err.message || err}`, "danger");
    return false;
  }
}

async function processExit(ticketId, amountPaid, paymentMethod) {
  try {
    const res = await fetch("/api/process-exit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticketId: ticketId,
        amountPaid: amountPaid,
        paymentMethod: paymentMethod,
      }),
    });
    const json = await res.json();
    if (!res.ok || json.status !== "ok") {
      throw new Error(json.message || "Process exit failed");
    }
    showNotification("Exit processed and payment recorded", "success");
    setTimeout(() => location.reload(), 800);
    return json;
  } catch (err) {
    console.error("processExit error", err);
    showNotification(`Exit failed: ${err.message || err}`, "danger");
    return null;
  }
}

// UI prompt helpers the templates can call directly
function promptProcessExit(ticketId) {
  const amount = prompt("Enter amount to pay (numeric)");
  if (amount === null) return; // cancelled
  const method = prompt(
    "Enter payment method (Cash, Credit Card, UPI, AppWallet)"
  );
  if (method === null) return;
  // basic validation
  const amtNum = parseFloat(amount);
  if (isNaN(amtNum) || amtNum < 0) {
    showNotification("Invalid amount", "warning");
    return;
  }
  processExit(ticketId, amtNum, method);
}

function promptSwapSpot(ticketId) {
  const newSpot = prompt("Enter new spot number to swap to (e.g. A12)");
  if (!newSpot) return;
  if (!confirm(`Swap ticket #${ticketId} to spot ${newSpot}?`)) return;
  swapSpot(ticketId, newSpot);
}

// expose the new helpers
window.ParkingSystem.getAvailableSpots = getAvailableSpots;
window.ParkingSystem.swapSpot = swapSpot;
window.ParkingSystem.processExit = processExit;
window.ParkingSystem.promptProcessExit = promptProcessExit;
window.ParkingSystem.promptSwapSpot = promptSwapSpot;

// --- Modal-based UI flows ---
async function openSwapModal(ticketId, lotId, currentSpotNumber) {
  // Fetch list of available spots for lot
  console.log("openSwapModal called with:", {
    ticketId,
    lotId,
    currentSpotNumber,
  });

  if (!lotId) {
    showNotification(
      "Cannot determine lot for this ticket. Make sure the ticket has a valid spot assigned.",
      "warning"
    );
    return;
  }
  try {
    const res = await fetch(`/api/available-spots-list/${lotId}`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const json = await res.json();
    console.log("Available spots response:", json);

    const select = document.getElementById("swapSpotSelect");
    select.innerHTML = "";

    // Add a placeholder
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.text = "Select spot...";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    if (json.spots && json.spots.length > 0) {
      json.spots.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.SpotNumber;
        opt.text = s.SpotNumber + " (ID " + s.SpotID + ")";
        select.appendChild(opt);
      });
    } else {
      // No available spots - add a disabled option explaining this
      const noSpots = document.createElement("option");
      noSpots.value = "";
      noSpots.text = "No available spots in this lot";
      noSpots.disabled = true;
      select.appendChild(noSpots);
      showNotification(
        `No available spots found in Lot ${lotId}. All spots may be occupied.`,
        "info"
      );
    }

    // store ticket id on confirm button
    document.getElementById("confirmSwapBtn").dataset.ticketId = ticketId;
    // show modal
    const swapModal = new bootstrap.Modal(document.getElementById("swapModal"));
    swapModal.show();
  } catch (err) {
    console.error("openSwapModal error", err);
    showNotification(
      "Failed to load available spots: " + err.message,
      "danger"
    );
  }
}

async function confirmSwapFromModal() {
  const btn = document.getElementById("confirmSwapBtn");
  const ticketId = parseInt(btn.dataset.ticketId, 10);
  const select = document.getElementById("swapSpotSelect");
  const newSpotNumber = select.value;
  if (!newSpotNumber) {
    showNotification("Please select a spot", "warning");
    return;
  }
  await swapSpot(ticketId, newSpotNumber);
}

async function openExitModal(ticketId) {
  try {
    const res = await fetch(`/api/estimate-exit/${ticketId}`);
    const json = await res.json();
    if (!res.ok || json.status !== "ok") {
      throw new Error(json.message || "Estimate failed");
    }
    // populate modal fields
    document.getElementById("exitTicketId").textContent = ticketId;
    document.getElementById("exitEstimatedTotal").textContent = formatCurrency(
      json.estimatedTotal
    );
    document.getElementById("exitAmountInput").value = json.estimatedTotal;
    // Store the required amount for validation
    document.getElementById("confirmExitBtn").dataset.ticketId = ticketId;
    document.getElementById("confirmExitBtn").dataset.requiredAmount =
      json.estimatedTotal;

    const exitModal = new bootstrap.Modal(document.getElementById("exitModal"));
    exitModal.show();
  } catch (err) {
    console.error("openExitModal error", err);
    showNotification("Failed to estimate exit total", "danger");
  }
}

async function confirmExitFromModal() {
  const btn = document.getElementById("confirmExitBtn");
  const ticketId = parseInt(btn.dataset.ticketId, 10);
  const requiredAmount = parseFloat(btn.dataset.requiredAmount);
  const amt = parseFloat(document.getElementById("exitAmountInput").value);
  const method = document.getElementById("exitMethodSelect").value || "Cash";

  if (isNaN(amt) || amt < 0) {
    showNotification("Invalid amount", "warning");
    return;
  }

  // Validate exact amount
  if (Math.abs(amt - requiredAmount) > 0.01) {
    showNotification(
      `Payment amount must match the required fee of ${formatCurrency(
        requiredAmount
      )}. Please pay the exact amount.`,
      "warning"
    );
    return;
  }

  await processExit(ticketId, amt, method);
}

window.ParkingSystem.openSwapModal = openSwapModal;
window.ParkingSystem.confirmSwapFromModal = confirmSwapFromModal;
window.ParkingSystem.openExitModal = openExitModal;
window.ParkingSystem.confirmExitFromModal = confirmExitFromModal;

// --- Helpers for creating lots and tickets via stored procedures ---
async function createLotWithDefaults(
  lotName,
  capacity,
  location = "",
  levels = 1
) {
  try {
    const res = await fetch("/api/create-lot-default", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        LotName: lotName,
        Capacity: capacity,
        Location: location,
        Levels: levels,
      }),
    });
    const json = await res.json();
    if (!res.ok || json.status !== "ok")
      throw new Error(json.message || "Create lot failed");
    showNotification("Lot created with default rates", "success");
    setTimeout(() => location.reload(), 700);
    return true;
  } catch (err) {
    console.error("createLotWithDefaults error", err);
    showNotification(`Create lot failed: ${err.message || err}`, "danger");
    return false;
  }
}

async function addTicketAndOccupy(
  licensePlate,
  spotId,
  rateId,
  entryTime = null
) {
  try {
    const res = await fetch("/api/add-ticket", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        LicensePlate: licensePlate,
        SpotID: spotId,
        RateID: rateId,
        EntryTime: entryTime,
      }),
    });
    const json = await res.json();
    if (!res.ok || json.status !== "ok")
      throw new Error(json.message || "Add ticket failed");
    showNotification("Ticket created and spot occupied", "success");
    setTimeout(() => location.reload(), 700);
    return true;
  } catch (err) {
    console.error("addTicketAndOccupy error", err);
    showNotification(`Add ticket failed: ${err.message || err}`, "danger");
    return false;
  }
}

window.ParkingSystem.createLotWithDefaults = createLotWithDefaults;
window.ParkingSystem.addTicketAndOccupy = addTicketAndOccupy;
