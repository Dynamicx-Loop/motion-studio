# Local dependencies and evidence

The documentation CSS, search, renderer and diagram are authored for Motion
Studio. System fonts are used; no font or icon service is contacted.

The existing report bundle contains Three.js r165, copyright 2010–2024 Three.js
Authors, SPDX-License-Identifier MIT. The builder reuses its existing
`inspectors/canonical-motion/vendor/three.module.js` and `OrbitControls.js`,
preserving their bytes and notices. The following MIT text applies to Three.js;
it does not grant a license to Motion Studio or the bundled research assets.

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the “Software”), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
> THE SOFTWARE.

Selected legacy figures, processed human geometry and robot geometry come from
already-local research artifacts. The build manifest identifies their paths and
SHA-256 hashes. They are not newly licensed for redistribution. SMPL-X, SOMA-X,
source datasets and robot assets retain their own terms. No new model weights,
raw source motions or external licensed media are downloaded by this builder.
