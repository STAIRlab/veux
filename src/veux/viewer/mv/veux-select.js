class ModelTable {
  /**
   * @param {{viewer:HTMLElement|string, tbody:HTMLElement|string, filter?:HTMLElement|string, count?:HTMLElement|string, emissive?:[number,number,number]}} opts
   */
  constructor(opts) {
    this.mv = this._getEl(opts.viewer);
    this.tbody = this._getEl(opts.tbody);
    this.filterEl = opts.filter ? this._getEl(opts.filter) : null;
    this.countEl = opts.count ? this._getEl(opts.count) : null;
    this.emissive = opts.emissive || [0.8, 0.2, 0.0];

    // state
    this.nodes = []; // { node, name, path }
    this.highlighted = null; // { node, materials: [{mat, orig}] }

    // bind
    this._onMVLoad = this._onMVLoad.bind(this);
    this._onFilter = this._onFilter.bind(this);

    this.mv.addEventListener('load', this._onMVLoad);
    if (this.filterEl) this.filterEl.addEventListener('input', this._onFilter);
  }

  // ————— public helpers —————
  destroy() {
    this.mv.removeEventListener('load', this._onMVLoad);
    if (this.filterEl) this.filterEl.removeEventListener('input', this._onFilter);
    this._clearHighlight();
    this.tbody.innerHTML = '';
    this.nodes = [];
  }

  // ————— internal —————
  _getEl(x) { return (typeof x === 'string') ? document.querySelector(x) : x; }

  _onMVLoad() {
    console.log('ModelTable: model loaded');
    const model = this.mv.model;
    if (!model) return;
    this.nodes = this._collectNodes(model);
    this._populate(this.nodes);
  }

  _onFilter() {
    const q = (this.filterEl?.value || '').trim().toLowerCase();
    const filtered = q
      ? this.nodes.filter(n => (n.name||'').toLowerCase().includes(q) || n.path.toLowerCase().includes(q))
      : this.nodes;
    this._populate(filtered);
  }

  _collectNodes(model) {
    const out = [];
    const root = model?.scene;
    console.log('ModelTable: collecting nodes from scene', root);
    if (!root) return out;

    const walk = (node, pathArr) => {

      const name = node.name || '(unnamed)';
      const path = [...pathArr, name].join(' / ');
      out.push({ node, name, path });
      const kids = (node.children || []);
      kids.forEach(child => walk(child, [...pathArr, name]));
    };
    walk(root, []);
    return out;
  }

  _populate(rows) {
    this.tbody.innerHTML = '';
    rows.forEach(entry => this.tbody.appendChild(this._makeRow(entry)));
    if (this.countEl) this.countEl.textContent = `${rows.length} / ${this.nodes.length} nodes`;
  }

  _makeRow(entry) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${entry.name}</td><td class="muted">${entry.path}</td>`;
    tr.addEventListener('click', (e) => {
      [...this.tbody.querySelectorAll('tr')].forEach(r => r.classList.remove('active'));
      tr.classList.add('active');
      this._highlight(entry.node);
      e.stopPropagation();
    });
    return tr;
  }

  _clearHighlight() {
    if (!this.highlighted) return;
    for (const {mat, orig} of this.highlighted.materials) {
      try { mat.setEmissiveFactor(orig); } catch (e) {}
    }
    this.highlighted = null;
  }

  _highlight(node) {
    if (!node) return;
    const model = this.mv.model;
    if (!model) return;

    // remove previous
    this._clearHighlight();

    // gather materials
    const mats = new Set();
    try {
      if (node.mesh != null && model.meshes) {
        const mesh = model.meshes[node.mesh];
        (mesh?.primitives || []).forEach(p => { if (p?.material != null) mats.add(model.materials[p.material]); });
      }
      if (node.primitives) {
        node.primitives.forEach(p => { if (p.material != null) mats.add(model.materials[p.material]); });
      }
    } catch (err) {
      console.warn('Could not enumerate materials for node', node, err);
    }

    const materials = [];
    mats.forEach(mat => {
      try {
        const orig = (mat.emissiveFactor && mat.emissiveFactor.length === 3) ? [...mat.emissiveFactor] : [0,0,0];
        materials.push({mat, orig});
        mat.setEmissiveFactor(this.emissive);
      } catch (e) {}
    });

    this.highlighted = { node, materials };
    this._focus(node);
  }

  _focus(node) {
    try {
      const m = node.worldMatrix || node.matrix;
      if (m && m.length === 16) {
        const x = m[12], y = m[13], z = m[14];
        this.mv.cameraTarget = `${x}m ${y}m ${z}m`;
      } else {
        this.mv.cameraTarget = 'auto';
      }
    } catch (_) {
      this.mv.cameraTarget = 'auto';
    }
  }
}
// class ModelTable {
//   constructor(opts) {
//     this.viewer = document.querySelector(opts.viewer);
//     this.tbody = document.querySelector(opts.tbody);
//     this.filter = document.querySelector(opts.filter);
//     this.count = document.querySelector(opts.count);
//     this.highlighted = null;

//     this.viewer.addEventListener('load', () => this.onLoad());
//   }

//   onLoad() {
//     const model = this.viewer.model;
//     if (!model) return;
//     this.nodes = this.getAllNodes(model);
//     if (this.nodes.length === 0) {
//       console.warn('No nodes found, using fallback names');
//       this.nodes = [{name:'Astronaut'},{name:'Helmet'},{name:'Visor'}];
//     }
//     this.populateTable(this.nodes);

//     this.filter.addEventListener('input', () => {
//       const q = this.filter.value.trim().toLowerCase();
//       const filtered = this.nodes.filter(n => (n.name||'').toLowerCase().includes(q));
//       this.populateTable(filtered);
//     });
//   }

//   focusNode(node) {
//     if (!node) return;
//     try {
//       const m = node.worldMatrix || node.matrix;
//       if (m && m.length === 16) {
//         const x = m[12], y = m[13], z = m[14];
//         this.viewer.cameraTarget = `${x}m ${y}m ${z}m`;
//       } else {
//         this.viewer.cameraTarget = 'auto';
//       }
//     } catch (_) {
//       this.viewer.cameraTarget = 'auto';
//     }
//   }

//   highlightNode(node) {
//     if (!node) return;
//     const model = this.viewer.model;
//     if (!model) return;

//     if (this.highlighted) {
//       for (const {mat, orig} of this.highlighted.materials) {
//         try { mat.setEmissiveFactor(orig); } catch(e) {}
//       }
//       this.highlighted = null;
//     }

//     const mats = new Set();
//     try {
//       if (node.mesh != null && model.meshes) {
//         const mesh = model.meshes[node.mesh];
//         (mesh?.primitives || []).forEach(p => { if (p?.material != null) mats.add(model.materials[p.material]); });
//       }
//       if (node.primitives) {
//         node.primitives.forEach(p => { if (p.material != null) mats.add(model.materials[p.material]); });
//       }
//     } catch (err) {
//       console.warn('Could not enumerate materials for node', node, err);
//     }

//     const materials = [];
//     mats.forEach(mat => {
//       try {
//         const orig = (mat.emissiveFactor && mat.emissiveFactor.length === 3)
//           ? [...mat.emissiveFactor]
//           : [0,0,0];
//         materials.push({mat, orig});
//         mat.setEmissiveFactor([0.8, 0.2, 0.0]);
//       } catch(e) {}
//     });

//     this.highlighted = { node, materials };
//     this.focusNode(node);
//   }

//   makeRow(node) {
//     const tr = document.createElement('tr');
//     tr.innerHTML = `<td>${node.name || '(unnamed)'}</td><td><button>Highlight</button></td>`;
//     tr.addEventListener('click', (e) => {
//       [...this.tbody.querySelectorAll('tr')].forEach(r => r.classList.remove('active'));
//       tr.classList.add('active');
//       this.highlightNode(node);
//       e.stopPropagation();
//     });
//     return tr;
//   }

//   populateTable(nodes) {
//     this.tbody.innerHTML = '';
//     nodes.forEach(n => this.tbody.appendChild(this.makeRow(n)));
//     this.count.textContent = `${nodes.length} nodes`;
//   }

//   getAllNodes(model) {
//     try {
//       return model?.scene?.children || [];
//     } catch (_) { return []; }
//   }
// }

// ——— bootstrap ———
const table = new ModelTable({
  viewer: '#veux-viewer',
  tbody:  '#rows',
  filter: '#filter',
  count:  '#count',
  // emissive: [1, 0.8, 0] // tweak if you want a brighter highlight
});