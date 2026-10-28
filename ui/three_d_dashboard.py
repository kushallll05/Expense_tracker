"""
Three.js 3D Interactive Financial Visualization Component.
Renders real-time interactive 3D financial core and orbiting category nodes
driven by actual database spending metrics.
"""
import json
from typing import List, Dict, Any
from src.config import CATEGORIES, CURRENCY_SYMBOL


def render_three_d_dashboard_html(category_data: List[Dict[str, Any]], total_expenses: float, height: int = 540) -> str:
    """
    Generates a standalone, responsive Three.js 3D dashboard HTML component.
    Receives real category spending records from the database.
    """
    # Prepare sanitized JSON data for JavaScript
    clean_nodes = []
    
    # If no expenses recorded yet, render sample skeleton categories so the 3D scene is alive
    if not category_data or total_expenses <= 0:
        default_cats = ["Food", "Shopping", "Transport", "Bills", "Groceries", "Entertainment", "Health"]
        for idx, cat in enumerate(default_cats):
            meta = CATEGORIES.get(cat, {})
            clean_nodes.append({
                "category": cat,
                "amount": 0.0,
                "percentage": round(100.0 / len(default_cats), 1),
                "count": 0,
                "color": meta.get("color", "#38bdf8"),
                "icon": meta.get("icon", "💎"),
                "is_empty": True,
            })
    else:
        for item in category_data:
            cat_name = item.get("category", "Other")
            meta = CATEGORIES.get(cat_name, {})
            clean_nodes.append({
                "category": cat_name,
                "amount": float(item.get("total_amount", 0.0)),
                "percentage": float(item.get("percentage", 0.0)),
                "count": int(item.get("count", 0)),
                "color": meta.get("color", "#38bdf8"),
                "icon": meta.get("icon", "💎"),
                "is_empty": False,
            })

    json_payload = json.dumps(clean_nodes)
    currency_symbol = CURRENCY_SYMBOL

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>3D Financial Ecosystem</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }}
    body, html {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #080c14;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }}
    #canvas-container {{
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
    }}

    /* Controls Overlay */
    .controls-bar {{
      position: absolute;
      top: 16px;
      right: 16px;
      display: flex;
      gap: 8px;
      z-index: 100;
    }}
    .ctrl-btn {{
      background: rgba(19, 27, 46, 0.75);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: #e2e8f0;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .ctrl-btn:hover {{
      background: rgba(56, 189, 248, 0.2);
      border-color: #38bdf8;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
    }}
    .ctrl-btn.active {{
      background: rgba(6, 182, 212, 0.35);
      border-color: #06b6d4;
    }}

    /* Title / Status Badge */
    .status-badge {{
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(19, 27, 46, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
      border-radius: 8px;
      padding: 6px 14px;
      color: #94a3b8;
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 100;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.3); opacity: 0.6; }}
    }}

    /* Dynamic Hover Tooltip */
    #tooltip {{
      position: absolute;
      display: none;
      pointer-events: none;
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 16px rgba(56, 189, 248, 0.25);
      backdrop-filter: blur(16px);
      border-radius: 10px;
      padding: 10px 14px;
      color: #f8fafc;
      font-size: 12px;
      z-index: 200;
      transform: translate(12px, 12px);
      transition: opacity 0.15s ease;
      min-width: 140px;
    }}
    #tooltip .tooltip-header {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
      font-size: 14px;
      margin-bottom: 4px;
      color: #38bdf8;
    }}
    #tooltip .tooltip-row {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 3px;
      color: #cbd5e1;
    }}

    /* Bottom Selected Node Card */
    #selection-card {{
      position: absolute;
      bottom: 16px;
      left: 16px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(56, 189, 248, 0.3);
      backdrop-filter: blur(16px);
      border-radius: 12px;
      padding: 12px 18px;
      color: #f8fafc;
      z-index: 100;
      max-width: 320px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }}
    #selection-card h4 {{
      font-size: 13px;
      font-weight: 600;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }}
    #selection-card p {{
      font-size: 12px;
      color: #94a3b8;
      line-height: 1.4;
    }}
  </style>

  <!-- Three.js and OrbitControls via CDN -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="canvas-container"></div>

  <!-- Top Badges & Controls -->
  <div class="status-badge">
    <div class="status-dot"></div>
    <span>3D Financial Orbit • Real-time Dynamics</span>
  </div>

  <div class="controls-bar">
    <button class="ctrl-btn active" id="btn-rotate">⏯️ Rotation</button>
    <button class="ctrl-btn" id="btn-reset">🎯 Reset Camera</button>
  </div>

  <!-- Tooltip -->
  <div id="tooltip">
    <div class="tooltip-header" id="tt-title">Food</div>
    <div class="tooltip-row">
      <span>Total Spent:</span>
      <strong id="tt-amount">{currency_symbol}0</strong>
    </div>
    <div class="tooltip-row">
      <span>Share:</span>
      <strong id="tt-pct">0%</strong>
    </div>
    <div class="tooltip-row">
      <span>Transactions:</span>
      <strong id="tt-count">0</strong>
    </div>
  </div>

  <!-- Selection Card -->
  <div id="selection-card">
    <h4 id="card-title">🪐 Financial Cosmos</h4>
    <p id="card-desc">Click or hover any glowing category node to inspect real spending distribution. Drag to orbit, scroll to zoom.</p>
  </div>

  <script>
    const categoryData = {json_payload};
    const currency = "{currency_symbol}";

    // Scene, Camera, Renderer
    const container = document.getElementById('canvas-container');
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x080c14, 0.035);

    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 6, 22);

    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // Orbit Controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 45;
    controls.minDistance = 6;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.8;

    // Ambient and Point Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const cyanLight = new THREE.PointLight(0x06b6d4, 2.5, 40);
    cyanLight.position.set(12, 10, 8);
    scene.add(cyanLight);

    const violetLight = new THREE.PointLight(0xa855f7, 2.5, 40);
    violetLight.position.set(-12, -8, -8);
    scene.add(violetLight);

    const coreLight = new THREE.PointLight(0x38bdf8, 3.0, 20);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    // ==================== 1. Central Core ====================
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner Glowing Core (Icosahedron)
    const coreGeo = new THREE.IcosahedronGeometry(2.0, 2);
    const coreMat = new THREE.MeshStandardMaterial({{
      color: 0x0ea5e9,
      emissive: 0x0369a1,
      roughness: 0.2,
      metalness: 0.8,
      wireframe: false,
    }});
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    // Outer Wireframe Cage
    const cageGeo = new THREE.IcosahedronGeometry(2.35, 1);
    const cageMat = new THREE.MeshBasicMaterial({{
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    }});
    const cageMesh = new THREE.Mesh(cageGeo, cageMat);
    coreGroup.add(cageMesh);

    // Orbital Rings
    const ringMat1 = new THREE.MeshBasicMaterial({{ color: 0x06b6d4, transparent: true, opacity: 0.25, side: THREE.DoubleSide }});
    const ringGeo1 = new THREE.TorusGeometry(8.5, 0.04, 16, 100);
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 3;
    scene.add(ring1);

    const ringMat2 = new THREE.MeshBasicMaterial({{ color: 0xa855f7, transparent: true, opacity: 0.2, side: THREE.DoubleSide }});
    const ringGeo2 = new THREE.TorusGeometry(10.5, 0.04, 16, 100);
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.y = Math.PI / 6;
    scene.add(ring2);

    // Background Particle Starfield
    const particlesCount = 800;
    const particlePositions = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount * 3; i += 3) {{
      particlePositions[i] = (Math.random() - 0.5) * 80;
      particlePositions[i + 1] = (Math.random() - 0.5) * 80;
      particlePositions[i + 2] = (Math.random() - 0.5) * 80;
    }}
    const particlesGeo = new THREE.BufferGeometry();
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particlesMat = new THREE.PointsMaterial({{
      color: 0x38bdf8,
      size: 0.12,
      transparent: true,
      opacity: 0.5,
    }});
    const starfield = new THREE.Points(particlesGeo, particlesMat);
    scene.add(starfield);

    // ==================== 2. Category Nodes ====================
    const categoryObjects = [];
    const nodeGroup = new THREE.Group();
    scene.add(nodeGroup);

    const numNodes = categoryData.length;
    const orbitRadius = 9.0;

    categoryData.forEach((item, index) => {{
      // Determine size based on percentage (scale between 0.65 and 1.6)
      const pct = Math.max(item.percentage || 0, 5);
      const radius = 0.6 + Math.sqrt(pct) * 0.18;

      // Position in 3D orbit using golden ratio distribution or circle
      const angle = (index / numNodes) * Math.PI * 2;
      const heightOffset = Math.sin(index * 1.8) * 2.5;
      const x = Math.cos(angle) * orbitRadius;
      const z = Math.sin(angle) * orbitRadius;
      const y = heightOffset;

      // Create Node Mesh
      const hexColor = parseInt(item.color.replace('#', '0x'), 16) || 0x38bdf8;
      const nodeGeo = new THREE.SphereGeometry(radius, 32, 32);
      const nodeMat = new THREE.MeshStandardMaterial({{
        color: hexColor,
        emissive: hexColor,
        emissiveIntensity: 0.35,
        roughness: 0.25,
        metalness: 0.7,
      }});
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.position.set(x, y, z);

      // Add a subtle wireframe halo around the orb
      const haloGeo = new THREE.SphereGeometry(radius * 1.25, 12, 12);
      const haloMat = new THREE.MeshBasicMaterial({{
        color: hexColor,
        wireframe: true,
        transparent: true,
        opacity: 0.22,
      }});
      const haloMesh = new THREE.Mesh(haloGeo, haloMat);
      nodeMesh.add(haloMesh);

      // Store metadata on mesh for raycaster
      nodeMesh.userData = {{
        ...item,
        baseScale: 1.0,
        originalEmissive: 0.35,
        orbitAngle: angle,
        orbitRadius: orbitRadius,
        orbitSpeed: 0.002 + (index % 3) * 0.001,
      }};

      nodeGroup.add(nodeMesh);
      categoryObjects.push(nodeMesh);
    }});

    // ==================== 3. Raycaster & Tooltip ====================
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let hoveredNode = null;
    const tooltip = document.getElementById('tooltip');

    function onMouseMove(event) {{
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      tooltip.style.left = event.clientX + 'px';
      tooltip.style.top = event.clientY + 'px';
    }}

    function onClick(event) {{
      if (hoveredNode) {{
        const data = hoveredNode.userData;
        document.getElementById('card-title').innerHTML = `${{data.icon || '🪐'}} ${{data.category}}`;
        document.getElementById('card-desc').innerHTML = 
          `<b>${{currency}}${{data.amount.toLocaleString()}}</b> spent across <b>${{data.count}}</b> transactions (${{data.percentage}}% of expenses). Click on the table below to filter by this category.`;
        
        // Pulse animation
        hoveredNode.scale.set(1.4, 1.4, 1.4);
        setTimeout(() => {{
          if (hoveredNode) hoveredNode.scale.set(1.2, 1.2, 1.2);
        }}, 200);
      }}
    }}

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('click', onClick);

    // ==================== 4. UI Controls ====================
    let isRotating = true;
    const btnRotate = document.getElementById('btn-rotate');
    const btnReset = document.getElementById('btn-reset');

    btnRotate.addEventListener('click', () => {{
      isRotating = !isRotating;
      controls.autoRotate = isRotating;
      btnRotate.classList.toggle('active', isRotating);
    }});

    btnReset.addEventListener('click', () => {{
      camera.position.set(0, 6, 22);
      controls.target.set(0, 0, 0);
      controls.update();
    }});

    window.addEventListener('resize', () => {{
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }});

    // ==================== 5. Animation Loop ====================
    const clock = new THREE.Clock();

    function animate() {{
      requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Core rotation and pulse
      coreGroup.rotation.y = elapsedTime * 0.25;
      coreGroup.rotation.x = Math.sin(elapsedTime * 0.3) * 0.15;
      const corePulse = 1.0 + Math.sin(elapsedTime * 2.0) * 0.04;
      coreMesh.scale.set(corePulse, corePulse, corePulse);

      ring1.rotation.z = elapsedTime * 0.1;
      ring2.rotation.z = -elapsedTime * 0.12;

      // Category nodes subtle orbital drift
      categoryObjects.forEach((node, idx) => {{
        if (isRotating) {{
          node.userData.orbitAngle += node.userData.orbitSpeed;
          const a = node.userData.orbitAngle;
          const r = node.userData.orbitRadius;
          node.position.x = Math.cos(a) * r;
          node.position.z = Math.sin(a) * r;
        }}
        // Gentle bobbing
        node.position.y += Math.sin(elapsedTime * 1.5 + idx) * 0.005;
      }});

      // Raycasting
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(categoryObjects, false);

      if (intersects.length > 0) {{
        const target = intersects[0].object;
        if (hoveredNode !== target) {{
          if (hoveredNode) {{
            hoveredNode.scale.set(1, 1, 1);
            hoveredNode.material.emissiveIntensity = hoveredNode.userData.originalEmissive;
          }}
          hoveredNode = target;
          hoveredNode.scale.set(1.22, 1.22, 1.22);
          hoveredNode.material.emissiveIntensity = 0.9;

          // Update tooltip
          const d = hoveredNode.userData;
          document.getElementById('tt-title').innerHTML = `${{d.icon || ''}} ${{d.category}}`;
          document.getElementById('tt-amount').innerText = `${{currency}}${{d.amount.toLocaleString()}}`;
          document.getElementById('tt-pct').innerText = `${{d.percentage}}%`;
          document.getElementById('tt-count').innerText = `${{d.count}} txns`;
          tooltip.style.display = 'block';
        }}
      }} else {{
        if (hoveredNode) {{
          hoveredNode.scale.set(1, 1, 1);
          hoveredNode.material.emissiveIntensity = hoveredNode.userData.originalEmissive;
          hoveredNode = null;
          tooltip.style.display = 'none';
        }}
      }}

      controls.update();
      renderer.render(scene, camera);
    }}

    animate();
  </script>
</body>
</html>
"""
    return html_template
