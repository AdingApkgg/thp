// Visible, opt-in private fixture instrumentation. No shader/precision edits.
export function installStageShaderObserver(canvas) {
  const nativeGetContext = canvas.getContext;
  const contexts = [], byContext = new WeakMap();
  let marker = null;
  function observe(gl) {
    if (byContext.has(gl)) return;
    const extension = gl.getExtension('WEBGL_debug_shaders');
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    const state = {id:contexts.length + 1, gl, extension, programs:[], errors:[], links:0, uses:0, draws:0, nextProgramId:1,
      programIds:new WeakMap(), uploadedSources:new WeakMap(), markers:[]};
    byContext.set(gl, state); contexts.push(state);
    const id = program => {
      if (!program) return null;
      if (!state.programIds.has(program)) state.programIds.set(program, state.nextProgramId++);
      return state.programIds.get(program);
    };
    const safely = (operation, label) => {
      try {return operation();} catch (error) {state.errors.push({label, error:String(error)}); return null;}
    };
    const shaderSource = gl.shaderSource, linkProgram = gl.linkProgram, useProgram = gl.useProgram;
    gl.shaderSource = function (...args) {
      const returned = Reflect.apply(shaderSource, this, args);
      safely(() => state.uploadedSources.set(args[0], args[1]), 'submitted shader record');
      return returned;
    };
    gl.linkProgram = function (...args) {
      const returned = Reflect.apply(linkProgram, this, args), program = args[0];
      safely(() => {
        const shaders = this.getAttachedShaders(program) || [];
        state.programs.push({programId:id(program), linkOrdinal:++state.links, marker,
          linked:this.getProgramParameter(program, this.LINK_STATUS), infoLog:this.getProgramInfoLog(program),
          shaders:shaders.map(shader => {
            const translated = extension ? safely(() => extension.getTranslatedShaderSource(shader), 'translated shader query') : null;
            return {type:this.getShaderParameter(shader, this.SHADER_TYPE),
              typeName:this.getShaderParameter(shader, this.SHADER_TYPE) === this.VERTEX_SHADER ? 'vertex' : 'fragment',
              compiled:this.getShaderParameter(shader, this.COMPILE_STATUS), infoLog:this.getShaderInfoLog(shader),
              submittedSource:state.uploadedSources.get(shader) ?? null, actualApiSource:this.getShaderSource(shader),
              translatedSource:translated, translatedStatus:!extension ? 'extension_unavailable' :
                translated === null ? 'query_failed' : translated.length === 0 ? 'empty_translation' : 'returned'};
          })});
      }, 'linked program query');
      return returned;
    };
    gl.useProgram = function (...args) {
      const returned = Reflect.apply(useProgram, this, args); ++state.uses;
      safely(() => state.markers.push({event:'use', marker, programId:id(args[0])}), 'used program record'); return returned;
    };
    for (const method of ['drawArrays', 'drawElements']) {
      const native = gl[method];
      gl[method] = function (...args) {
        const returned = Reflect.apply(native, this, args); ++state.draws;
        safely(() => state.markers.push({event:method, marker, args, programId:id(this.getParameter(this.CURRENT_PROGRAM))}), 'draw program query');
        return returned;
      };
    }
    state.gpu = {vendor:gl.getParameter(gl.VENDOR), renderer:gl.getParameter(gl.RENDERER),
      unmaskedAvailable:!!debug, unmaskedVendor:debug ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL) : null,
      unmaskedRenderer:debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : null,
      version:gl.getParameter(gl.VERSION), shadingLanguageVersion:gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
      debugShadersExtensionAvailable:!!extension, contextAttributes:gl.getContextAttributes()};
  }
  canvas.getContext = function (...args) {
    const context = Reflect.apply(nativeGetContext, this, args);
    if (context && ['webgl', 'experimental-webgl', 'webgl2'].includes(args[0])) observe(context);
    return context;
  };
  return {
    mark(value){marker = value;},
    async snapshot() {
      const digest = async text => text === null ? null : Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))), b => b.toString(16).padStart(2, '0')).join('');
      const output = [];
      for (const state of contexts) {
        const programs = [];
        for (const row of state.programs) {
          const shaders = [];
          for (const shader of row.shaders) shaders.push({...shader,
            submittedSourceSha256:await digest(shader.submittedSource), actualApiSourceSha256:await digest(shader.actualApiSource),
            translatedSourceSha256:await digest(shader.translatedSource)});
          programs.push({...row, shaders});
        }
        output.push({id:state.id, gpu:state.gpu, programs, programEvents:state.markers, observerErrors:state.errors,
          linkCalls:state.links, useCalls:state.uses, drawCalls:state.draws,
          actualShaderSourcesObserved:programs.length > 0,
          translatedShadersObserved:programs.some(p => p.shaders.some(s => s.translatedStatus === 'returned'))});
      }
      return {contexts:output, readsActualAttachedShaders:true, extensionUnavailableIsNegative:true,
        nativeMethodsArgumentsAndReturnsPreserved:true, consumesGlErrorState:false,
        scope:'Actual linked-context API queries captured by this visible Run fixture. Translation is reported only when WEBGL_debug_shaders returns a nonempty string. No guessed backend shader or production arithmetic mutation.'};
    },
  };
}
