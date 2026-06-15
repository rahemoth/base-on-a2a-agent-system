import eventBus from '@/core/event-bus.js';
import storage from '@/core/storage.js';

/**
 * Registers a plugin with the bus. Plugin may provide hooks
 * for: init, beforeCommit, afterCommit, beforePush, afterPush,
 * beforePull, afterPull, onKeyBound, onKeyConflict, onError.
 */
export async function registerPlugin(name, pluginFactory) {
  const settings = storage.getPluginSettings(name);
  const plugin = await pluginFactory({ bus: eventBus, settings });

  const hooks = [
    'init',
    'beforeCommit', 'afterCommit',
    'beforePush', 'afterPush',
    'beforePull', 'afterPull',
    'onKeyBound', 'onKeyConflict',
    'onError',
  ];

  for (const hook of hooks) {
    if (typeof plugin[hook] === 'function') {
      eventBus.on(hook, plugin[hook]);
    }
  }

  if (typeof plugin.init === 'function') {
    await plugin.init();
  }

  return plugin;
}
