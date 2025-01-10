State Space Model of Structural Dynamics
----------------------------------------

.. figure:: figures/si_msmdof.png
   :alt: MDOF Structure

   MDOF Structure

When an multiple degree-of-freedom (MDOF) system is subject to multiple
support excitation, such as in the figure above, the displacement vector
is extended to include the support DOF. An `equation of
motion <#equation-of-motion>`__ is derived as follows.

Begin by forming a partitioned equation of dynamic equilibrium for all
the DOF:

Partitioned Equation of Dynamic Equilibrium
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::


   \begin{bmatrix} \mathbf{m} & \mathbf{m}_{g} \\ \mathbf{m}^T_{g} & \mathbf{m}_{gg} \end{bmatrix}
   \begin{bmatrix} \mathbf{\ddot{u}}^{t}_{f} \\ \mathbf{\ddot{u}}_{g} \end{bmatrix}
   +
   \begin{bmatrix} \mathbf{c} & \mathbf{c}_{g} \\ \mathbf{c}^T_{g} & \mathbf{c}_{gg} \end{bmatrix}
   \begin{bmatrix} \mathbf{\dot{u}}^{t}_{f} \\ \mathbf{\dot{u}}_{g} \end{bmatrix}
   +
   \begin{bmatrix} \mathbf{k} & \mathbf{k}_{g} \\ \mathbf{k}^T_{g} & \mathbf{k}_{gg} \end{bmatrix}
   \begin{bmatrix} \mathbf{u}^{t}_{f} \\ \mathbf{u}_{g} \end{bmatrix}
   =
   \begin{bmatrix} \mathbf{0} \\ \mathbf{p}_{g} \end{bmatrix}

where the subscript :math:`g` indicates support DOF, the subscript
:math:`f` indicates structural DOF, and the superscript :math:`t`
indicates the total of quasi-static (:math:`\mathbf{u}^{s}_{f}`, due to
static application of support displacements) and dynamic
(:math:`\mathbf{u}_{f}`, evaluated by dynamic analysis) structural
displacements.

Taking the first half of the partitioned equilibrium, separating the
structural displacements
(:math:`\mathbf{u}^{t}_{f}=\mathbf{u}^{s}_{f}+\mathbf{u}_{f}`), and
moving all :math:`\mathbf{u}_{g}` and :math:`\mathbf{u}^{s}_{f}` terms
to the right side,

.. math::


   \mathbf{m}\mathbf{\ddot{u}}_{f} + \mathbf{c}\mathbf{\dot{u}}_{f} + \mathbf{k}\mathbf{u}_{f}
   = -(\mathbf{m}\mathbf{\ddot{u}}^{s}_{f}+\mathbf{m}_{g}\mathbf{\ddot{u}}_{g})
   -(\mathbf{c}\mathbf{\dot{u}}^{s}_{f}+\mathbf{c}_{g}\mathbf{\dot{u}}_{g})
   -(\mathbf{k}\mathbf{u}^{s}_{f}+\mathbf{k}_{g}\mathbf{u}_{g})

The term
:math:`(\mathbf{k}\mathbf{u}^{s}_{f}+\mathbf{k}_{g}\mathbf{u}_{g})=\mathbf{0}`
due to static equilibrium, allowing the term to be dropped and giving
:math:`\mathbf{u}^{s}_{f} = \mathbf{-k}^{-1}\mathbf{k}_{g}\mathbf{u}_{g} = \mathbf{\iota u}_{g}`;
the term
:math:`(\mathbf{c}\mathbf{\dot{u}}^{s}_{f}+\mathbf{c}_{g}\mathbf{\dot{u}}_{g})`
is dropped because it is usually small relative to the inertia term; and
the term :math:`\mathbf{m}_{g}\mathbf{\ddot{u}}_{g}` is dropped because
mass is usually neglected at supports.

The equilibrium equation thus simplifies.

Equation of Motion
^^^^^^^^^^^^^^^^^^

.. math::


   \begin{aligned}
       \mathbf{M\ddot{u}}_{f}(t) + \mathbf{Z\dot{u}}_{f}(t) + \mathbf{Ku}_{f}(t) &= -\mathbf{M\iota}\mathbf{\ddot{u}}_{g}(t) \\
       \mathbf{m}\mathbf{\ddot{u}}_{f} + \mathbf{c}\mathbf{\dot{u}}_{f} + \mathbf{k}\mathbf{u}_{f}
       &= -\mathbf{m}\mathbf{\iota}\mathbf{\ddot{u}}_{g}
   \end{aligned}

Hence, the following equation presents the continuous linear
time-invariant (LTI) state-space representation of a structural system.

Continuous LTI State-Space Representation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::


   \begin{aligned}
       \mathbf{\dot{x}} &= \mathbf{A}_{c}\mathbf{x} + \mathbf{B}_{c}\mathbf{u} \\
       \begin{bmatrix} \mathbf{\dot{u}}_{f}(t) \\ \mathbf{\ddot{u}}_{f}(t) \end{bmatrix}
       &=
       \begin{bmatrix} \mathbf{0} & \mathbf{I} \\ -\mathbf{M}^{-1}\mathbf{K} & -\mathbf{M}^{-1}\mathbf{Z} \end{bmatrix}
       \begin{bmatrix} \mathbf{u}_{f}(t) \\ \mathbf{\dot{u}}_{f}(t) \end{bmatrix}
       +
       \begin{bmatrix} \mathbf{0} \\ -\mathbf{\iota} \end{bmatrix}
       \mathbf{\ddot{u}}_{g}(t) \\ \\
       \mathbf{y} &= \mathbf{Cx} + \mathbf{Du} \\        
       \mathbf{\ddot{u}}_{f}(t) &= 
       \begin{bmatrix} -\mathbf{M}^{-1}\mathbf{K} & -\mathbf{M}^{-1}\mathbf{Z} \end{bmatrix}
       \begin{bmatrix} \mathbf{u}_{f}(t) \\ \mathbf{\dot{u}}_{f}(t) \end{bmatrix}
       +
       \begin{bmatrix} -\mathbf{\iota} \end{bmatrix}
       \mathbf{\ddot{u}}_{g}(t)
   \end{aligned}

In order to move from the continuous to the discrete case, the
coefficients :math:`\mathbf{A}_{c}` and :math:`\mathbf{B}_{c}` are
transformed by solving the first-order differential equation with the
signal’s value held constant between time steps (“zero-order hold
method”). The coefficients :math:`\mathbf{C}` and :math:`\mathbf{D}` are
unchanged. The results are shown in the following equation.

.. figure:: figures/si_discretize.png
   :alt: Signal Discretization

   Signal Discretization

Discrete LTI State-Space Representation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::


   \begin{aligned}
       \mathbf{x}_{k+1} &= \mathbf{Ax}_{k} + \mathbf{Bu}_{k} \\
       \mathbf{y}_{k} &= \mathbf{Cx}_{k} + \mathbf{Du}_{k} \\        
   \end{aligned}

.. math::


   \mathbf{x}_{k} = \mathbf{x}(k\Delta t), \hspace{1cm} \mathbf{u}_{k} = \mathbf{u}(k\Delta t), \hspace{1cm} \mathbf{y}_{k} = \mathbf{y}(k\Delta t)

.. math::


   \mathbf{A} = e^{\mathbf{A}_{c}\Delta t}, \hspace{1cm} \mathbf{B} = \int_{0}^{\Delta t}{e^{\mathbf{A}_{c}\tau}}\mathbf{B}_{c}d\tau

where:

.. math::


   \begin{aligned}
       \mathbf{A} & \text{: discrete state transition matrix} \\
       \mathbf{B} & \text{: discrete input influence matrix} \\
       \mathbf{C} & \text{: output influence matrix} \\
       \mathbf{D} & \text{: direct transmission or feed-through matrix}
   \end{aligned}
