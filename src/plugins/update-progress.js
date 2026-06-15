import { PUSH_PROGRESS, PULL_PROGRESS, KEY_BIND_RESULT, SYNC_ERROR } from '@/core/event-bus.js';

const CIRCLE_RADIUS = 12;
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS;
const FONT_SIZE = 13;
const PADDING_X = 10;
const PADDING_Y = 4;
const LINE_HEIGHT = 20;
const MIN_WIDTH = 80;

export default function updateProgressPlugin({ bus }) {
  let overlay = null;
  let circleEl = null;
  let messageEl = null;
  let containerEl = null;

  function ensureOverlay() {
    if (overlay) return;

    overlay = document.createElement('div');
    overlay.id = 'sync-overlay';
    overlay.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.35);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999;
      transition: opacity 0.3s ease;
    `;

    containerEl = document.createElement('div');
    containerEl.style.cssText = `
      display: flex; flex-direction: column; align-items: center; gap: 16px;
      color: #fff; font-size: ${FONT_SIZE}px; font-family: system-ui, sans-serif;
      text-shadow: 0 1px 3px rgba(0,0,0,0.5);
    `;

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('width', String(CIRCLE_RADIUS * 2 + 4));
    svg.setAttribute('height', String(CIRCLE_RADIUS * 2 + 4));

    const bgCircle = document.createElementNS(svgNS, 'circle');
    bgCircle.setAttribute('cx', String(CIRCLE_RADIUS + 2));
    bgCircle.setAttribute('cy', String(CIRCLE_RADIUS + 2));
    bgCircle.setAttribute('r', String(CIRCLE_RADIUS));
    bgCircle.setAttribute('fill', 'none');
    bgCircle.setAttribute('stroke', 'rgba(255,255,255,0.3)');
    bgCircle.setAttribute('stroke-width', '3');
    svg.appendChild(bgCircle);

    circleEl = document.createElementNS(svgNS, 'circle');
    circleEl.setAttribute('cx', String(CIRCLE_RADIUS + 2));
    circleEl.setAttribute('cy', String(CIRCLE_RADIUS + 2));
    circleEl.setAttribute('r', String(CIRCLE_RADIUS));
    circleEl.setAttribute('fill', 'none');
    circleEl.setAttribute('stroke', '#fff');
    circleEl.setAttribute('stroke-width', '3');
    circleEl.setAttribute('stroke-linecap', 'round');
    circleEl.setAttribute('stroke-dasharray', String(CIRCLE_CIRCUMFERENCE));
    circleEl.setAttribute('stroke-dashoffset', String(CIRCLE_CIRCUMFERENCE));
    circleEl.style.transition = 'stroke-dashoffset 0.3s ease';
    circleEl.style.transform = 'rotate(-90deg)';
    circleEl.style.transformOrigin = 'center';
    svg.appendChild(circleEl);

    messageEl = document.createElement('div');
    messageEl.style.cssText = `
      min-width: ${MIN_WIDTH}px; text-align: center;
      padding: ${PADDING_Y}px ${PADDING_X}px;
      background: rgba(0,0,0,0.4); border-radius: 6px;
    `;

    containerEl.appendChild(svg);
    containerEl.appendChild(messageEl);
    overlay.appendChild(containerEl);
    document.body.appendChild(overlay);
  }

  function updateProgress({ current, total, message }) {
    ensureOverlay();
    overlay.style.display = 'flex';
    overlay.style.opacity = '1';
    const fraction = total > 0 ? current / total : 0;
    const offset = CIRCLE_CIRCUMFERENCE * (1 - fraction);
    circleEl.setAttribute('stroke-dashoffset', String(offset));
    messageEl.textContent = message;
  }

  function showMessage(text, isError = false) {
    ensureOverlay();
    overlay.style.display = 'flex';
    overlay.style.opacity = '1';
    circleEl.setAttribute('stroke-dashoffset', '0');
    messageEl.textContent = text;
    messageEl.style.color = isError ? '#ff6b6b' : '#fff';
  }

  function hideOverlay() {
    if (overlay) {
      overlay.style.opacity = '0';
      setTimeout(() => {
        overlay.style.display = 'none';
      }, 300);
    }
  }

  return {
    init() {},

    onKeyBound({ key, language, modifiedKey }) {
      console.log(`[Keybind] ${key} → ${language}/${modifiedKey}`);
    },

    onKeyConflict({ key, language, modifiedKey, existingLanguage }) {
      console.warn(
        `[Keybind conflict] ${key}: ${language}/${modifiedKey} conflicts with existing ${existingLanguage}`
      );
    },

    beforePush() {
      updateProgress({ current: 0, total: 1, message: '同步中...' });
    },

    afterPush({ pushed }) {
      const msg = pushed ? '同步完成 ✓' : '远端已是最新';
      showMessage(msg);
      setTimeout(hideOverlay, 1200);
    },

    beforePull() {
      updateProgress({ current: 0, total: 1, message: '拉取中...' });
    },

    afterPull({ pulled }) {
      const msg = pulled ? '拉取完成 ✓' : '已是最新';
      showMessage(msg);
      setTimeout(hideOverlay, 1200);
    },

    onError({ stage, error }) {
      const msg = `同步出错 (${stage}): ${error.message}`;
      showMessage(msg, true);
      setTimeout(hideOverlay, 3000);
    },
  };
}
