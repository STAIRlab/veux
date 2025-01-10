<!-- ---
title: Power Spectral Density
author: Chrystal Chern
date: Monday, November 27, 2023
... -->

# Power Spectral Density

The power spectral density is the norm of the Fourier transform. In a way, it measures energy content at each frequency of response.

It is also the averaged(?) Fourier transform of the autocorrelation.

## Norm of Fourier Transform

The power spectral density, $P(f)$, of a signal $y(t)$, is

$$\begin{aligned}
P(f) &= \frac{1}{T}
\int_{-T}^{T}{
    \left| Y_{T}(f) \right|^{2}df
}
\end{aligned}$$

Where the Fourier transform $Y_{T}(f)$ of $y_{T}(t)$ is defined as:
$$\begin{aligned}
Y_{T}(f) &= \mathcal{F}\left\{y_{T}(t)\right\} = \int_{-T}^{T}{
    e^{-i2\pi ft}y_{T}(t)dt
}
\end{aligned}$$

where $f \in \mathbb{R}_{+}$ is frequency in Hertz, and $t \in \mathbb{R}_{+}$ is time in seconds.

**question.**
$$\begin{aligned}
y_{T}(t) = \begin{bmatrix}
y(t) \\
y(t+\Delta t) \\
y(t+2\Delta t) \\
\vdots \\
y(t+(T-1)\Delta t) \\
\end{bmatrix}
\in \mathbb{R}^{T} ~~\textbf{??}
\end{aligned}$$

## Fourier Transform of Autocorrelation

Autocorrelation, discrete:

$$\begin{aligned}
R_{yy} &\approx \frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{Y}_{p}^{*}(k), ~~N \gg 0
\end{aligned}$$

$$
\begin{aligned}
\mathbf{Y}_{p}(k) &= \begin{bmatrix} \mathbf{y}_{p}(k) & \mathbf{y}_{p}(k+1) & \cdots & \mathbf{y}_{p}(k+N-1) \end{bmatrix} \\
&= \begin{bmatrix}
\mathbf{y}(k)     & \mathbf{y}(k+1) & \cdots & \mathbf{y}(k+N-1)\\
\mathbf{y}(k+1)   & \mathbf{y}(k+2) & \cdots & \mathbf{y}(k+N)  \\
\vdots            & \vdots          & \ddots & \vdots \\
\mathbf{y}(k+p-1) & \mathbf{y}(k+p) & \cdots & \mathbf{y}(k+N+p-2)
\end{bmatrix}
\end{aligned}
$$

```{=tex}
\pagebreak
```

Autocorrelation, continuous:

$$\begin{aligned}
R_{yy}(\tau)
&= \mathbb{E}\left\{\mathbf{y}(t+\tau)\mathbf{y}^{*}(t)\right\} \\
&= \int_{-\infty}^{\infty}{\mathbf{y}(t+\tau)\mathbf{y}^{*}(t)f_{y}(t)dt}
\\
&= \int_{-\infty}^{\infty}{\mathbf{y}(t+\tau)\mathbf{y}^{*}(t)dt} ~~\textbf{??}
\\
&= \underset{T \rightarrow \infty}{\lim}\frac{1}{T}\int_{-\infty}^{\infty}{\mathbf{y}_{T}^{*}(t-\tau)\mathbf{y}_{T}(t)dt} ~~\textbf{??}
\end{aligned}$$

Fourier transform of this autocorrelation:
$$\begin{aligned}
\mathcal{F}\left\{R_{yy}(\tau)\right\} &= \mathbf{R}_{yy}(f) \\
&= \int_{-\infty}^{\infty}e^{-i2\pi ft}R_{yy}(\tau)d\tau \\
&= \int_{-\infty}^{\infty}e^{-i2\pi ft}\left[ 
    \underset{T \rightarrow \infty}{\lim}\frac{1}{T}\int_{-\infty}^{\infty}{\mathbf{y}_{T}^{*}(t-\tau)\mathbf{y}_{T}(t)dt}
\right](\tau)d\tau \\
&= \underset{N \rightarrow \infty}{\lim}\frac{\left( \Delta t \right)^{2}}{T}\left| \sum_{n=-N}^{N} y_{n} e^{-i2\pi fn\Delta t} \right|^{2} \\
&\approx \underset{T \rightarrow \infty}{\lim}{\frac{1}{T}\left| Y_{T}(f) \right|^{2}}
\end{aligned}$$

Averaged...**??** Fourier transform of this autocorrelation:
$$\begin{aligned}
P &= \int_{-\infty}^{\infty}{\mathbf{R}_{yy}(f) df}
&= \int_{-\infty}^{\infty}{
    \underset{T \rightarrow \infty}{\lim}
    \frac{1}{T}
    \left| Y_{T}(f) \right|^{2}df
    }
\end{aligned}$$