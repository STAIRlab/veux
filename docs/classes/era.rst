
Eigensystem Realization Algorithm (ERA)
---------------------------------------


As shown in the previous section, a structural system’s dynamic behavior
can be represented by the four coefficients
(:math:`\mathbf{A},\mathbf{B},\mathbf{C},\mathbf{D}`) of its discrete
LTI state-space representation. The `Ho-Kalman
Algorithm <https://doi.org/10.1524/auto.1966.14.112.545>`__, or
`Eigensystem Realization Algorithm <https://doi.org/10.2514/3.20031>`__,
produces a *reduced order model* for these four coefficients,
(:math:`\mathbf{\tilde{A}},\mathbf{\tilde{B}},\mathbf{\tilde{C}},\mathbf{\tilde{D}}`),
based on an impulse input and its corresponding response output. Then,
modal properties can be extracted from :math:`\mathbf{\tilde{A}}` and
:math:`\mathbf{\tilde{C}}`.

With the discrete LTI model, a unit impulse input with zero initial
conditions produces an output of constants
(:math:`\mathbf{D,CB,CAB,...,CA}^{k-1}\mathbf{B}`). These constants are
called *Markov parameters* because they must be unique for a given
system – there is only one possible output for a unit impulse input.

.. math::


   \begin{aligned}
       \mathbf{x}_{k+1} &= \mathbf{Ax}_{k} + \mathbf{Bu}_{k} \\
       \mathbf{y}_{k} &= \mathbf{Cx}_{k} + \mathbf{Du}_{k} \\        
   \end{aligned}

.. math::


   \begin{aligned}
       \mathbf{u}_{0},\mathbf{u}_{1},\mathbf{u}_{2},...,\mathbf{u}_{k} &= \mathbf{I,0,0,...,0} \\
       \mathbf{x}_{0},\mathbf{x}_{1},\mathbf{x}_{2},...,\mathbf{x}_{k} &= \mathbf{0,B,AB,...,A}^{k-1}\mathbf{B} \\
       \mathbf{y}_{0},\mathbf{y}_{1},\mathbf{y}_{2},...,\mathbf{y}_{k} &= \mathbf{D,CB,CAB,...,CA}^{k-1}\mathbf{B} \\
   \end{aligned}

Knowing that the impulse response output data directly give the Markov
parameters, the data can then be stacked into the generalized blockwise
Hankel matrix :math:`\mathbf{H}`:

.. math::


   \mathbf{H}
   =
   \begin{bmatrix}
       \mathbf{y}_{1}     & \mathbf{y}_{2}        & \cdots   & \mathbf{y}_{m_{c}}          \\
       \mathbf{y}_{2}     & \mathbf{y}_{3}        & \cdots   & \mathbf{y}_{m_{c}+1}        \\
       \vdots             & \vdots                & \ddots   & \vdots                      \\
       \mathbf{y}_{m_{o}} & \mathbf{y}_{m_{o}+1}  & \cdots   & \mathbf{y}_{m_{o}+m_{c}-1}  \\
   \end{bmatrix}
   =
   \begin{bmatrix}
       \mathbf{CB}                     & \mathbf{CAB}                  & \cdots  & \mathbf{CA}^{m_{c}-1}\mathbf{B}       \\
       \mathbf{CAB}                    & \mathbf{CA}^{2}\mathbf{B}     & \cdots  & \mathbf{CA}^{m_{c}}\mathbf{B}         \\
       \vdots                          & \vdots                        & \ddots  & \vdots                                \\
       \mathbf{CA}^{m_{o}-1}\mathbf{B} & \mathbf{CA}^{m_{o}}\mathbf{B} & \cdots  & \mathbf{CA}^{m_{c}+m_{o}-2}\mathbf{B} \\
   \end{bmatrix}
   =
   \mathbf{\mathcal{OC}}

where :math:`\mathbf{\mathcal{O}}` and :math:`\mathbf{\mathcal{C}}` are
the observability and controllability matrices of the system:

.. math::


   \mathbf{\mathcal{O}} = \begin{bmatrix}
       \mathbf{C} \\ \mathbf{CA} \\ \mathbf{CA}^{2} \\ \vdots \\ \mathbf{CA}^{m_{o}-1}
   \end{bmatrix}, \hspace{1cm}
   \mathbf{\mathcal{C}} = \begin{bmatrix} \mathbf{B} & \mathbf{AB} & \mathbf{A}^{2}\mathbf{B} & \cdots & \mathbf{A}^{m_{c}-1}\mathbf{B}  \end{bmatrix}

The shifted Hankel matrix, :math:`\mathbf{H'}` (one time step ahead of
:math:`\mathbf{H}`), is shown below:

.. math::


   \mathbf{H'}
   =
   \begin{bmatrix}
       \mathbf{y}_{2}       & \mathbf{y}_{3}        & \cdots   & \mathbf{y}_{m_{c}+1}        \\
       \mathbf{y}_{3}       & \mathbf{y}_{4}        & \cdots   & \mathbf{y}_{m_{c}+2}        \\
       \vdots               & \vdots                & \ddots   & \vdots                      \\
       \mathbf{y}_{m_{o}+1} & \mathbf{y}_{m_{o}+2}  & \cdots   & \mathbf{y}_{m_{o}+m_{c}}    \\
   \end{bmatrix}
   =
   \begin{bmatrix}
       \mathbf{CAB}                    & \mathbf{CA}^{2}\mathbf{B}     & \cdots  & \mathbf{CA}^{m_{c}}\mathbf{B}          \\
       \mathbf{CA}^{2}\mathbf{B}       & \mathbf{CA}^{3}\mathbf{B}     & \cdots  & \mathbf{CA}^{m_{c}+1}\mathbf{B}        \\
       \vdots                          & \vdots                        & \ddots  & \vdots                                 \\
       \mathbf{CA}^{m_{o}}\mathbf{B}   & \mathbf{CA}^{m_{o}+1}\mathbf{B} & \cdots  & \mathbf{CA}^{m_{c}+m_{o}-1}\mathbf{B}\\
   \end{bmatrix}
   =
   \mathbf{\mathcal{O}A\mathcal{C}}

By taking the dominant terms of the singular value decomposition 
of :math:`\mathbf{H}`, and transforming the relationship between
:math:`\mathbf{H} = \mathbf{\mathcal{OC}}` and
:math:`\mathbf{H'} = \mathbf{\mathcal{O}A\mathcal{C}}`, a reduced-order
model is constructed as follows:

.. math::


   \mathbf{H} = \mathbf{U}\Sigma\mathbf{V}^{H} = 
   \begin{bmatrix} \mathbf{\tilde{U}} & \mathbf{U}_{t} \end{bmatrix}
   \begin{bmatrix} \tilde{\Sigma} & \mathbf{0} \\ \mathbf{0} & \Sigma_{t} \end{bmatrix}
   \begin{bmatrix} \mathbf{\tilde{V}}^{H} \\ \mathbf{V}_{t}^{H} \end{bmatrix}
   \approx \mathbf{\tilde{U}}\tilde{\Sigma}\mathbf{\tilde{V}}^{H}

where the superscript :math:`H` denotes conjugate transpose and the
subscript :math:`t` indicates elements to be truncated such that only
the first :math:`r` dominant singular values in :math:`\tilde{\Sigma}`
are retained,

.. math::


   \begin{aligned}
       \mathbf{\tilde{A}} &= \tilde{\Sigma}^{-1/2}\mathbf{\tilde{U}}^{H}\mathbf{H'\tilde{V}}\tilde{\Sigma}^{-1/2} \\        
       \mathbf{\tilde{B}} &= \tilde{\Sigma}^{1/2}\mathbf{\tilde{V}}^{H}
                           \begin{bmatrix} \mathbf{I}_{q} \\ \mathbf{0} \end{bmatrix} \\
       \mathbf{\tilde{C}} &= \begin{bmatrix} \mathbf{I}_{p} & \mathbf{0} \end{bmatrix} \mathbf{\tilde{U}}\tilde{\Sigma}^{1/2} \\
       \mathbf{\tilde{D}} &= \mathbf{y}_{0}
   \end{aligned}

where :math:`p` indicates the number of outputs and :math:`q` the number
of inputs, and

.. math::


   \begin{aligned}
       \mathbf{\tilde{x}}_{k+1} &= \mathbf{\tilde{A}\tilde{x}}_{k} + \mathbf{\tilde{B}u}_{k} \\
       \mathbf{y}_{k} &= \mathbf{\tilde{C}\tilde{x}}_{k} + \mathbf{\tilde{D}u}_{k}. \\
   \end{aligned}
