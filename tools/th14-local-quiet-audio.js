// Local preview fixture only. This file is never copied into the release site.
// AudioNode.connect/disconnect semantics: MDN Web API reference; final live
// destination edges alone are replaced by a native zero-gain edge.
(() => {
  'use strict';
  const node = globalThis.AudioNode;
  const marker = Symbol.for('th14.workspace.quiet-audio.v1');
  if (node && !node.prototype[marker]) {
    const connectDescriptor = Object.getOwnPropertyDescriptor(node.prototype, 'connect');
    const disconnectDescriptor = Object.getOwnPropertyDescriptor(node.prototype, 'disconnect');
    const nativeConnect = connectDescriptor.value, nativeDisconnect = disconnectDescriptor.value;
    const gains = new WeakMap();
    Object.defineProperty(node.prototype, 'connect', {...connectDescriptor, value:function connect(destination) {
      const args = Array.from(arguments), context = this.context;
      if (!context || destination !== context.destination) return Reflect.apply(nativeConnect, this, args);
      // Offline rendering is signal generation rather than speaker output.
      if (typeof globalThis.OfflineAudioContext === 'function' && context instanceof globalThis.OfflineAudioContext) return Reflect.apply(nativeConnect, this, args);
      let gain = gains.get(this);
      if (!gain) {
        gain = context.createGain(); gain.gain.value = 0;
        Reflect.apply(nativeConnect, gain, [destination]); // Native call avoids recursion.
        gains.set(this, gain);
      }
      args[0] = gain; // All output/input indices and extra arguments are retained.
      const returned = Reflect.apply(nativeConnect, this, args);
      return returned === gain ? destination : returned; // Includes legacy undefined.
    }});
    Object.defineProperty(node.prototype, 'disconnect', {...disconnectDescriptor, value:function disconnect() {
      const args = Array.from(arguments);
      if (args.length && this.context && args[0] === this.context.destination && gains.has(this)) args[0] = gains.get(this);
      return Reflect.apply(nativeDisconnect, this, args);
    }});
    Object.defineProperty(node.prototype, marker, {value:true});
  }
  const label = () => {
    if (document.getElementById('th14-workspace-quiet')) return;
    const badge = document.createElement('aside'); badge.id = 'th14-workspace-quiet';
    badge.textContent = node ? '本机测试静音' : '本机静音适配不可用';
    badge.title = '仅本机预览输出为零；混音器仍运行，不作为原版音频等价证明。';
    badge.style.cssText = 'position:fixed;right:8px;bottom:8px;z-index:2147483647;padding:4px 8px;background:#17212de8;color:#fff;font:12px system-ui;pointer-events:none';
    document.body.appendChild(badge);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', label, {once:true});
  else label();
})();
