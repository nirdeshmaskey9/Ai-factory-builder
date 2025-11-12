// Compact trio status display for chat sidebar
(function() {
  async function updateTrioStatus() {
    try {
      const res = await fetch('/ui/system_status');
      const data = await res.json();
      const trio = data.trio_health || {};
      
      function updateRole(role, elementId) {
        const el = document.getElementById(elementId);
        if (!el) return;
        const roleData = trio[role] || {};
        const healthy = roleData.healthy === true;
        const dot = el.querySelector('span');
        const text = el.querySelector('span + span') || el;
        
        if (dot) {
          dot.className = `w-2 h-2 rounded-full ${healthy ? 'bg-green-500' : 'bg-red-500'}`;
        }
        
        // Update text content
        const model = roleData.model || '';
        const shortModel = model.split(':')[0] || (model.length > 15 ? model.substring(0, 15) + '...' : model);
        const roleName = role.charAt(0).toUpperCase() + role.slice(1);
        const statusText = healthy ? '● healthy' : '● down';
        const fullText = `${roleName} ${statusText} | ${shortModel}`;
        
        // Find text span (next sibling of dot)
        const textSpan = el.querySelector('span + span');
        if (textSpan) {
          textSpan.textContent = fullText;
        } else if (el.childNodes.length > 1) {
          el.childNodes[1].textContent = fullText;
        }
      }
      
      updateRole('strategist', 'trio-strategist');
      updateRole('memory', 'trio-memory');
      updateRole('executor', 'trio-executor');
    } catch (e) {
      console.debug('Trio status update error:', e);
    }
  }
  
  // Update on load and every 30 seconds
  updateTrioStatus();
  setInterval(updateTrioStatus, 30000);
})();

