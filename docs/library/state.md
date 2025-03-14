
```{eval-rst}  
.. _state:
```

# States

Many methods of the Artist class accept a `state` parameter. 

## `state`

The `state` parameter can be one of several types:

- `dict` maps node tags to node displacements
- `callable` maps node tags to node displacements. A common example is to pass the [`nodeDisp`](https://xara.so/user/manual/output/nodeDisp.html) method

## `position`/`rotation`

Alternatively, distinct `position` and `rotation` parameters may be passed.
`rotation` should be a callable like [`nodeRotation`](https://xara.so/user/manual/output/nodeRotation.html)

