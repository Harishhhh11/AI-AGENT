/*
 * AI Receptionist embed widget.
 *
 * Usage:
 * <script src="https://YOUR-PLATFORM/widget.js" data-agent="your-agent-slug"></script>
 *
 * The iframe keeps the customer chat isolated from the host website and
 * avoids sharing the website's cookies, storage, or JavaScript context.
 */
(function () {
  var script = document.currentScript;
  if (!script) return;

  var agent = script.getAttribute("data-agent");
  if (!agent) {
    console.error("AI Receptionist widget: data-agent is required.");
    return;
  }

  var platformOrigin = new URL(script.src, window.location.href).origin;
  var iframe = document.createElement("iframe");
  iframe.src = platformOrigin + "/chat/" + encodeURIComponent(agent);
  iframe.title = "AI receptionist";
  iframe.setAttribute("loading", "lazy");
  iframe.style.cssText = [
    "position:fixed",
    "right:20px",
    "bottom:20px",
    "width:min(390px,calc(100vw - 32px))",
    "height:min(620px,calc(100dvh - 32px))",
    "border:0",
    "border-radius:20px",
    "box-shadow:0 20px 55px rgba(15,23,42,.28)",
    "z-index:2147483647",
    "background:#fff",
    "display:none",
  ].join(";");

  var button = document.createElement("button");
  button.type = "button";
  button.setAttribute("aria-label", "Open AI receptionist");
  button.textContent = "Chat with us";
  button.style.cssText = [
    "position:fixed",
    "right:20px",
    "bottom:20px",
    "border:0",
    "border-radius:999px",
    "padding:14px 18px",
    "background:#4f46e5",
    "color:#fff",
    "font:600 14px/1 system-ui,sans-serif",
    "cursor:pointer",
    "box-shadow:0 12px 28px rgba(79,70,229,.35)",
    "z-index:2147483647",
  ].join(";");
  button.onclick = function () {
    var isOpen = iframe.style.display !== "none";
    iframe.style.display = isOpen ? "none" : "block";
    button.textContent = isOpen ? "Chat with us" : "Close chat";
    button.setAttribute("aria-label", isOpen ? "Open AI receptionist" : "Close AI receptionist");
  };

  document.body.appendChild(iframe);
  document.body.appendChild(button);
})();
