# Tree_001 single-tree trial

Source: user-provided `Tree_001.zip`: ASCII FBX 7.3 and `Vegetation_Palette_001.png` (512×512).

`tree-001.glb` preserves the three named meshes and UVs with one embedded, shared palette texture/material. Assimp triangulates the FBX; source centimeters are multiplied by 0.01, and Max Z-up coordinates become glTF Y-up `(x, z, -y)`. UV V is converted to glTF texture coordinates. No artistic rescaling: bounds are about 6.14 × 8.76 × 5.81 meters, 1,284 triangles.

Only the nearest visible, non-fruit broadleaf to Hina's cave is replaced (about 13.04m from the cave center). Its original root transform and separately registered colliders are retained. Its original mesh remains as fallback if loading fails. This tree skips the existing wind and box batching; bark/leaves use the existing occlusion pipeline and the stump remains opaque. Existing renderer/shadow quality settings apply.

The adjacent vendor directory contains the Three.js r165 GLTF loader and its utility dependency, matching the game's embedded Three.js revision; license included. No external model/texture CDN is needed at runtime.
