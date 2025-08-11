.. _motions:

Motions
^^^^^^^

The ``veux.Motion`` class is used to draw animation frames. 
This page covers how to create, configure, and display animations of structural
simulations performed with OpenSeesRT.


.. class:: Motion


Examples
--------

.. code-block:: python

    import numpy as np
    import veux
    from math import sin, cos

    # ---------------------------------------------------------
    # 1) Build a simple finite element "beam" for visualization
    # ---------------------------------------------------------
    def create_simple_beam(ndm=3):
        """
        Creates a trivial 3D beam model with a fixed support at node 1
        and a free end at node 2, just for demonstration. 
        Returns the model object.
        """
        import opensees.openseespy as ops

        length = 1.0
        # Create a model with 2 nodes, each having 6 DOF (3D)
        model = ops.Model(ndm=ndm, ndf=6)
        model.node(1, (0.0, 0.0, 0.0))
        model.node(2, (length, 0.0, 0.0))

        # Fix node 1
        model.fix(1, 1,1,1, 1,1,1)

        # Just a dummy section & element so we can visualize a 'beam'
        E, I = 1.0, 2.0
        sec_tag = 1
        model.section("FrameElastic", sec_tag, 
                      E=E, G=1.0, A=2.0,
                      "-J", 2.0, "-Iy", I, "-Iz", I, "-Ay", 2.0, "-Az", 2.0)
        transf_tag = 1
        model.geomTransf("Linear", transf_tag, 0, 0, 1)
        model.element("ElasticBeamColumn", 1, (1, 2),
                      section=sec_tag,
                      transform=transf_tag)

        return model

    # ---------------------------------------------------------
    # 2) Create an Artist for drawing the beam
    # ---------------------------------------------------------
    model = create_simple_beam()
    artist = veux.create_artist(model,
                                vertical=2,  # y-axis is 'vertical' in this setup
                                model_config=dict(
                                    extrude_outline="square",
                                    extrude_scale=0.5
                                ))
    artist.draw_axes()
    artist.draw_outlines()

    # ---------------------------------------------------------
    # 3) Define exact (closed-form) solutions for rotation & position
    #    under a constant moment M about the z-axis
    # ---------------------------------------------------------
    E, I = 1.0, 2.0
    L    = 1.0


    def exact_position_rotation(M):
        """
        Returns two callable objects:
        - position(node) -> (x, y, z)
        - rotation(node) -> (qx, qy, qz, qw) with scalar last
        representing the beam's deformation under a constant moment M.
        """
        def position(node):
            # nodeCoord(1) -> (0.0, 0.0, 0.0)
            # nodeCoord(2) -> (L,   0.0, 0.0)
            xi = model.nodeCoord(node)[0]
            theta = xi * M / (E * I)

            # For M = 0, avoid dividing by zero
            if abs(M) < 1e-12:
                return (xi, 0.0, 0.0)

            x_def = xi + (E * I / M) * sin(theta)
            y_def = (E * I / M) * (cos(theta) - 1.0)
            return (x_def, y_def, 0.0)

        def rotation(node):
            xi = model.nodeCoord(node)[0]
            theta = xi * M / (E * I)
            # Rotation about z-axis by angle theta:
            # quaternion with scalar last -> (0, 0, sin(theta/2), cos(theta/2))
            return (0.0, 0.0, sin(theta / 2.0), cos(theta / 2.0))


        return position, rotation

    # ---------------------------------------------------------
    # 4) Animate using veux.Motion
    #    We vary M from 0 to 2 (dimensionless) to show large rotations
    # ---------------------------------------------------------
    from veux.motion import Motion

    motion = Motion(artist)
    moments = np.linspace(0, 2.0, 50)
    for M in moments:
        pos_func, rot_func = exact_position_rotation(M)
        # Draw the beam outlines at this "load" configuration
        motion.draw_outlines(position=pos_func, rotation=rot_func)
        motion.advance()

    # Insert the motion into the canvas and serve interactively
    motion.add_to(artist.canvas)
    veux.serve(artist)


