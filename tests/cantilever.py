import veux.frame.extrude
render = veux.frame.extrude._render

L = 10

def model(nodes, yvec):
    return {
        "StructuralAnalysisModel": {
              "geometry": {
                  "nodes": [
                      {"name": 1, "crd": list(nodes[0])},
                      {"name": 2, "crd": list(nodes[1])}
                  ],
                  "elements": [
                      {"name": 3, "type": "ElasticBeam3d", "nodes": [2, 1], "yvec": yvec}
                  ]
              }
          }
        }

for nodes, yvects in (
       (((0, 0, 0), (L, 0, 0)),
        ((0, 1, 0), # sideways if --vert 3
         (0, 0, 1), # sideways if --vert 2
         (0, 1, 1))),

       (((0, 0, 0), (0, L, 0)),
        ((1, 0, 0),
         (0, 0, 1),
         (1, 0, 1))),

       (((0, 0, 0), (0, 0, L)),
        ((0, 1, 0), # sideways if --vert 3
         (1, 0, 0), # sideways if --vert 2
         (1, 1, 0))),

#      (((0, 0, 0), (0, L, L)),
#       ((0, 1, 0), # sideways if --vert 3
#        (1, 0, 0), # sideways if --vert 2
#        (1, 1, 0))),

#      (((0, 0, 0), (L, L, 0)),
#       ((0, 1, 0), # sideways if --vert 3
#        (1, 0, 0), # sideways if --vert 2
#        (1, 1, 0))),

#      (((0, 0, 0), (L, 0, L)),
#       ((0, 1, 0), # sideways if --vert 3
#        (1, 0, 0), # sideways if --vert 2
#        (1, 1, 0))),

#      (((0, 0, 0), (L, L, L)),
#       ((0, 1, 0), # sideways if --vert 3
#        (1, 0, 0), # sideways if --vert 2
#        (1, 1, 0))),
       ):
    for yvec in yvects:
        render(model(nodes, yvec),
               canvas="gltf",
               extrude_outline="tee",
               extrude=True,
               objects=dict(sections=dict(scale=10))
        )


