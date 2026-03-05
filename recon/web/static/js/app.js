// Viral Command Recon — Shared JS utilities
// Minimal — most logic is inline in templates

/**
 * Format a number with commas
 */
function formatNumber(n) {
    if (!n) return '0';
    return n.toLocaleString();
}

/**
 * Relative time display
 */
function timeAgo(dateStr) {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = (now - date) / 1000;

    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
    return date.toLocaleDateString();
}
